"""Valida el conjunto de evaluacion contra los documentos (plan-data-engineer, paso 8).

Comprueba que datos/preguntas_evaluacion_green.csv:
- tiene las columnas del contrato (plan-equipo, seccion 5);
- tiene id unicos y tipo valido;
- cada fuente_esperada existe en documentos/ (vacia solo en abstencion);
- cada termino de terminos_clave aparece, sin distinguir mayusculas, en el
  texto de su fuente_esperada (filas que no son de abstencion);
- si existe datos/banco_preguntas.csv, cada pregunta del banco tiene fila con
  el mismo id, tipo y pregunta.

Uso, desde la raiz del repo:

    python scripts/validar_evaluacion.py

Termina con codigo 1 si encuentra algun problema. Solo biblioteca estandar.
"""
import argparse
import csv
import sys
from pathlib import Path

COLUMNAS = ["id", "tipo", "pregunta", "respuesta_esperada",
            "terminos_clave", "fuente_esperada"]
TIPOS = {"pais", "kpi", "ranking", "comparacion", "explicacion", "abstencion"}


def leer_csv(ruta):
    with Path(ruta).open(encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        return list(lector.fieldnames or []), list(lector)


def validar(ruta_evaluacion, carpeta_documentos, ruta_banco=None):
    errores = []
    columnas, filas = leer_csv(ruta_evaluacion)
    if columnas != COLUMNAS:
        return [f"columnas {columnas}, se esperaban {COLUMNAS}"]

    vistos = set()
    for numero, fila in enumerate(filas, start=2):
        ident = (fila["id"] or "").strip()
        donde = f"fila {numero} (id {ident or '?'})"
        if not ident:
            errores.append(f"{donde}: id vacio")
        elif ident in vistos:
            errores.append(f"{donde}: id repetido")
        vistos.add(ident)

        tipo = (fila["tipo"] or "").strip()
        if tipo not in TIPOS:
            errores.append(f"{donde}: tipo {tipo!r} no valido")
        if not (fila["pregunta"] or "").strip():
            errores.append(f"{donde}: pregunta vacia")
        if not (fila["respuesta_esperada"] or "").strip():
            errores.append(f"{donde}: respuesta_esperada vacia")

        terminos = [t.strip() for t in (fila["terminos_clave"] or "").split("|") if t.strip()]
        if not terminos:
            errores.append(f"{donde}: terminos_clave vacio")

        fuente = (fila["fuente_esperada"] or "").strip()
        if tipo == "abstencion":
            if fuente:
                errores.append(f"{donde}: abstencion no lleva fuente_esperada")
            continue
        if not fuente:
            errores.append(f"{donde}: falta fuente_esperada")
            continue
        ruta_fuente = Path(carpeta_documentos) / fuente
        if not ruta_fuente.is_file():
            errores.append(f"{donde}: {fuente} no existe en {carpeta_documentos}")
            continue
        texto = ruta_fuente.read_text(encoding="utf-8").lower()
        for termino in terminos:
            if termino.lower() not in texto:
                errores.append(f"{donde}: el termino {termino!r} no aparece en {fuente}")

    if ruta_banco and Path(ruta_banco).is_file():
        _, banco = leer_csv(ruta_banco)
        por_id = {f["id"].strip(): f for f in filas}
        for pregunta in banco:
            ident = pregunta["id"].strip()
            fila = por_id.get(ident)
            if fila is None:
                errores.append(f"banco id {ident}: sin fila en el conjunto de evaluacion")
                continue
            for campo in ("tipo", "pregunta"):
                if fila[campo].strip() != pregunta[campo].strip():
                    errores.append(f"id {ident}: {campo} distinto al del banco")
    return errores


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--evaluacion", default="datos/preguntas_evaluacion_green.csv", type=Path)
    parser.add_argument("--documentos", default="documentos", type=Path)
    parser.add_argument("--banco", default="datos/banco_preguntas.csv", type=Path)
    args = parser.parse_args(argv)

    errores = validar(args.evaluacion, args.documentos, args.banco)
    if not args.banco.is_file():
        print(f"Aviso: no existe {args.banco}; no se comprobo la cobertura del banco.")
    for error in errores:
        print(f"FAIL  {error}")
    if errores:
        print(f"\n{len(errores)} problemas encontrados")
        return 1
    print("PASS  conjunto de evaluacion coherente con los documentos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
