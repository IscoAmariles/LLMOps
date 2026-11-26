"""Ejecuta el conjunto de evaluacion contra la API y guarda la evidencia.

Uso (desde la raiz del proyecto, con la API levantada):

    python app/evaluacion.py datos/preguntas_evaluacion_green.csv --top-k 3 --temperatura 0.2
    python app/evaluacion.py --help

Por cada pregunta guarda la respuesta, las fuentes recuperadas, tokens y
tiempos, y dos chequeos automaticos de primera pasada:

- ``acierto_terminos``: todos los ``terminos_clave`` (separados por ``|``)
  aparecen en la respuesta, sin distinguir mayusculas.
- ``hit_fuente``: ``fuente_esperada`` esta entre las fuentes recuperadas
  (``rango_fuente`` dice en que posicion; sirve para hit@1 y hit@3).

La clasificacion final (correcta / incompleta / inventada) sigue siendo
MANUAL: estos chequeos solo la aceleran.

Con ``--mlflow`` la corrida queda como un run del experimento
``Evaluacion_RAG_Green`` (parametros, metricas y el JSON como artefacto).
"""
import argparse
import csv
import json
import math
import re
import sys
import time
from datetime import datetime
from pathlib import Path

API_URL = "http://localhost:8000/preguntar"
RUTA_CSV = Path("datos/preguntas_evaluacion_green.csv")
RUTA_META_INDICE = Path("datos/indice_meta.json")
RUTA_PROCEDENCIA = Path("datos/fuente/PROCEDENCIA.md")
FRASE_ABSTENCION = "información suficiente"
EXPERIMENTO_MLFLOW = "Evaluacion_RAG_Green"


# ---------------------------------------------------------------------------
# Logica pura (probada en tests/test_evaluacion.py)
# ---------------------------------------------------------------------------
def leer_preguntas(ruta, ids=None, tipos=None):
    with Path(ruta).open(encoding="utf-8", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    if ids:
        filas = [f for f in filas if f["id"] in ids]
    if tipos:
        filas = [f for f in filas if f.get("tipo") in tipos]
    return filas


def acierto_terminos(respuesta, terminos_clave):
    """True si todos los terminos (separados por |) estan en la respuesta."""
    terminos = [t.strip().lower() for t in (terminos_clave or "").split("|") if t.strip()]
    if not terminos:
        return None
    texto = (respuesta or "").lower()
    return all(t in texto for t in terminos)


def rango_fuente(fuentes, fuente_esperada):
    """Posicion (1-based) de la fuente esperada entre las recuperadas, o None."""
    if not fuente_esperada:
        return None
    for posicion, fuente in enumerate(fuentes, start=1):
        if fuente["fuente"] == fuente_esperada:
            return posicion
    return None


def se_abstuvo(respuesta):
    return FRASE_ABSTENCION in (respuesta or "").lower()


def percentil(valores, p):
    """Percentil por rango mas cercano (p entre 0 y 100)."""
    valores = sorted(v for v in valores if v is not None)
    if not valores:
        return None
    indice = max(0, math.ceil(p / 100 * len(valores)) - 1)
    return valores[indice]


def _tasa(valores):
    valores = [v for v in valores if v is not None]
    return round(sum(1 for v in valores if v) / len(valores), 4) if valores else None


def _media(valores):
    valores = [v for v in valores if v is not None]
    return round(sum(valores) / len(valores), 4) if valores else None


def resumir(resultados, top_k):
    """Agregados globales y por tipo de pregunta."""
    def agregar(grupo):
        validos = [r for r in grupo if not r.get("error")]
        con_fuente = [r for r in validos if r.get("fuente_esperada")]
        resumen = {
            "n": len(grupo),
            "errores": len(grupo) - len(validos),
            "acierto_terminos": _tasa(r["acierto_terminos"] for r in validos),
            "hit_at_1": _tasa(r["rango_fuente"] == 1 for r in con_fuente),
            "tokens_entrada_medio": _media(r["tokens_entrada"] for r in validos),
            "tokens_salida_medio": _media(r["tokens_salida"] for r in validos),
            "duracion_media": _media(r["duracion"] for r in validos),
            "duracion_p95": percentil([r["duracion"] for r in validos], 95),
        }
        if top_k >= 3:
            resumen["hit_at_3"] = _tasa(
                r["rango_fuente"] is not None and r["rango_fuente"] <= 3
                for r in con_fuente)
        resumen[f"hit_at_{top_k}"] = _tasa(r["hit_fuente"] for r in con_fuente)
        no_abst = [r for r in validos if r.get("tipo") != "abstencion"]
        resumen["abstencion_indebida"] = sum(1 for r in no_abst if r["se_abstuvo"])
        return resumen

    por_tipo = {}
    for resultado in resultados:
        por_tipo.setdefault(resultado.get("tipo", "sin_tipo"), []).append(resultado)
    return {
        "global": agregar(resultados),
        "por_tipo": {tipo: agregar(grupo) for tipo, grupo in sorted(por_tipo.items())},
    }


def commit_corpus(ruta=RUTA_PROCEDENCIA):
    """Commit del ETL del que sale el snapshot (de PROCEDENCIA.md)."""
    try:
        texto = Path(ruta).read_text(encoding="utf-8")
    except OSError:
        return "desconocido"
    coincidencia = re.search(r"\|\s*Commit\s*\|\s*`([0-9a-f]{7,40})`", texto)
    return coincidencia.group(1)[:7] if coincidencia else "desconocido"


def chunker_indice(ruta=RUTA_META_INDICE):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8")).get("chunker", "desconocido")
    except (OSError, ValueError):
        return "desconocido"


# ---------------------------------------------------------------------------
# Ejecucion contra la API
# ---------------------------------------------------------------------------
def evaluar_fila(fila, top_k, temperatura, api_url, repeticion=1):
    import requests

    base = {
        "id": fila["id"],
        "tipo": fila.get("tipo", ""),
        "pregunta": fila["pregunta"],
        "esperada": fila.get("respuesta_esperada", ""),
        "terminos_clave": fila.get("terminos_clave", ""),
        "fuente_esperada": fila.get("fuente_esperada", ""),
        "repeticion": repeticion,
        "top_k": top_k,
        "temperatura": temperatura,
    }
    inicio = time.perf_counter()
    try:
        respuesta = requests.post(
            api_url,
            json={"pregunta": fila["pregunta"], "top_k": top_k, "temperatura": temperatura},
            timeout=360,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()
    except requests.RequestException as error:
        return {**base, "error": str(error), "duracion": time.perf_counter() - inicio,
                "acierto_terminos": None, "hit_fuente": None, "rango_fuente": None,
                "se_abstuvo": False, "tokens_entrada": None, "tokens_salida": None}

    fuentes = [{"fuente": f["fuente"], "fragmento": f["fragmento"],
                "similitud": round(f["similitud"], 4)} for f in datos["fuentes"]]
    rango = rango_fuente(fuentes, base["fuente_esperada"])
    return {
        **base,
        "modelo": datos.get("modelo"),
        "generada": datos["respuesta"],
        "fuentes": fuentes,
        "rango_fuente": rango,
        "hit_fuente": rango is not None if base["fuente_esperada"] else None,
        "acierto_terminos": acierto_terminos(datos["respuesta"], base["terminos_clave"]),
        "se_abstuvo": se_abstuvo(datos["respuesta"]),
        "tokens_entrada": datos["tokens_entrada"],
        "tokens_salida": datos["tokens_salida"],
        "duracion_ollama": datos["duracion_ollama"],
        "duracion_generacion": datos["duracion_generacion"],
        "tiempo_recuperacion": datos["tiempo_recuperacion"],
        "duracion": time.perf_counter() - inicio,
        "error": None,
    }


def registrar_mlflow(args, resultados, resumen, ruta_salida):
    import mlflow

    mlflow.set_tracking_uri(args.mlflow_uri)
    mlflow.set_experiment(EXPERIMENTO_MLFLOW)
    modelo = next((r.get("modelo") for r in resultados if r.get("modelo")), "desconocido")
    with mlflow.start_run(run_name=args.etiqueta or None):
        mlflow.log_params({
            "modelo": modelo,
            "top_k": args.top_k,
            "temperatura": args.temperatura,
            "chunker": chunker_indice(),
            "corpus_commit": commit_corpus(),
            "conjunto": Path(args.csv).name,
            "repeticiones": args.repeticiones,
            "n_preguntas": len({r["id"] for r in resultados}),
        })
        metricas = {}
        for clave, valor in resumen["global"].items():
            if isinstance(valor, (int, float)) and valor is not None:
                metricas[clave] = valor
        for tipo, agregados in resumen["por_tipo"].items():
            for clave in ("acierto_terminos", "hit_at_1", "hit_at_3"):
                if agregados.get(clave) is not None:
                    metricas[f"{tipo}_{clave}"] = agregados[clave]
        mlflow.log_metrics(metricas)
        mlflow.log_artifact(str(ruta_salida))


def imprimir_resumen(resumen):
    columnas = ["n", "errores", "acierto_terminos", "hit_at_1", "hit_at_3",
                "tokens_entrada_medio", "duracion_p95", "abstencion_indebida"]
    print("\n" + "tipo".ljust(13) + "".join(c[:14].rjust(15) for c in columnas))
    filas = list(resumen["por_tipo"].items()) + [("GLOBAL", resumen["global"])]
    for tipo, agregados in filas:
        celdas = []
        for columna in columnas:
            valor = agregados.get(columna)
            celdas.append(("-" if valor is None else f"{valor:.3f}" if isinstance(valor, float)
                           else str(valor)).rjust(15))
        print(tipo.ljust(13) + "".join(celdas))


def construir_parser():
    parser = argparse.ArgumentParser(description="Evalua el RAG con un conjunto de preguntas.")
    parser.add_argument("csv", nargs="?", default=str(RUTA_CSV),
                        help=f"Conjunto de evaluacion (por defecto {RUTA_CSV})")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--temperatura", type=float, default=0.2)
    parser.add_argument("--salida", help="JSON de resultados (por defecto datos/resultados_<fecha>.json)")
    parser.add_argument("--repeticiones", type=int, default=1,
                        help="Veces que se repite cada pregunta (experimento de temperatura)")
    parser.add_argument("--ids", help="Solo estas preguntas, p. ej. 1,3,15")
    parser.add_argument("--tipos", help="Solo estos tipos, p. ej. pais,kpi")
    parser.add_argument("--api-url", default=API_URL)
    parser.add_argument("--mlflow", action="store_true", help="Registrar la corrida en MLflow")
    parser.add_argument("--mlflow-uri", default="http://localhost:5000")
    parser.add_argument("--etiqueta", help="Nombre del run en MLflow")
    return parser


def main(argv=None):
    args = construir_parser().parse_args(argv)
    filas = leer_preguntas(
        args.csv,
        ids=set(args.ids.split(",")) if args.ids else None,
        tipos=set(args.tipos.split(",")) if args.tipos else None,
    )
    if not filas:
        print("No hay preguntas que evaluar con esos filtros.")
        return 1

    resultados = []
    for repeticion in range(1, args.repeticiones + 1):
        for fila in filas:
            resultado = evaluar_fila(fila, args.top_k, args.temperatura, args.api_url, repeticion)
            resultados.append(resultado)
            estado = "ERROR" if resultado["error"] else (
                f"terminos={resultado['acierto_terminos']} rango={resultado['rango_fuente']}")
            print(f"[{repeticion}] Pregunta {fila['id']} ({resultado['tipo']}): {estado} "
                  f"{resultado['duracion']:.1f}s")

    resumen = resumir(resultados, args.top_k)
    ruta_salida = Path(args.salida or f"datos/resultados_{datetime.now():%Y%m%d_%H%M%S}.json")
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    ruta_salida.write_text(json.dumps({
        "parametros": {"csv": args.csv, "top_k": args.top_k, "temperatura": args.temperatura,
                       "repeticiones": args.repeticiones, "chunker": chunker_indice(),
                       "corpus_commit": commit_corpus()},
        "resumen": resumen,
        "resultados": resultados,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    imprimir_resumen(resumen)
    print(f"\nResultados en {ruta_salida}")
    if args.mlflow:
        registrar_mlflow(args, resultados, resumen, ruta_salida)
        print(f"Run registrado en MLflow ({EXPERIMENTO_MLFLOW})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
