"""Pruebas de la logica pura de app/evaluacion.py (sin API ni MLflow)."""
import evaluacion as ev
from conftest import escribir_csv

COLUMNAS = ["id", "tipo", "pregunta", "respuesta_esperada", "terminos_clave", "fuente_esperada"]
FUENTES = [{"fuente": "kpis.txt"}, {"fuente": "pais_NOR.txt"}, {"fuente": "pais_URY.txt"}]


def resultado(tipo="pais", acierto=True, rango=1, abst=False, duracion=1.0, error=None,
              fuente="pais_NOR.txt"):
    return {"tipo": tipo, "acierto_terminos": acierto, "rango_fuente": rango,
            "hit_fuente": (rango is not None) if fuente else None, "se_abstuvo": abst,
            "tokens_entrada": 100, "tokens_salida": 20, "duracion": duracion,
            "error": error, "fuente_esperada": fuente}


def test_acierto_terminos_todos_sin_mayusculas():
    assert ev.acierto_terminos("Noruega tiene 90.9 %", "90.9|noruega") is True
    assert ev.acierto_terminos("Noruega tiene 90 %", "90.9|noruega") is False
    assert ev.acierto_terminos("algo", "") is None


def test_rango_fuente():
    assert ev.rango_fuente(FUENTES, "pais_NOR.txt") == 2
    assert ev.rango_fuente(FUENTES, "pais_ARG.txt") is None
    assert ev.rango_fuente(FUENTES, "") is None


def test_se_abstuvo():
    assert ev.se_abstuvo("No existe información suficiente en los documentos.")
    assert not ev.se_abstuvo("Noruega tiene 90.9 %.")


def test_percentil():
    assert ev.percentil(list(range(1, 101)), 95) == 95
    assert ev.percentil([3.0], 95) == 3.0
    assert ev.percentil([], 95) is None


def test_resumir_por_tipo_y_hits():
    resultados = [
        resultado(rango=1),
        resultado(rango=3, acierto=False),
        resultado(rango=None, acierto=False),
        resultado(tipo="abstencion", rango=None, abst=True, fuente=""),
        resultado(tipo="kpi", abst=True, acierto=False),  # se abstuvo sin deber
        resultado(error="timeout", acierto=None, rango=None),
    ]
    resumen = ev.resumir(resultados, top_k=3)
    pais = resumen["por_tipo"]["pais"]
    assert pais["n"] == 4 and pais["errores"] == 1
    assert pais["hit_at_1"] == round(1 / 3, 4)
    assert pais["hit_at_3"] == round(2 / 3, 4)
    assert pais["acierto_terminos"] == round(1 / 3, 4)
    # la abstencion no cuenta para hit@k (no tiene fuente esperada)
    assert resumen["por_tipo"]["abstencion"]["hit_at_1"] is None
    assert resumen["global"]["abstencion_indebida"] == 1


def test_resumir_sin_hit3_si_top_k_1():
    resumen = ev.resumir([resultado()], top_k=1)
    assert "hit_at_3" not in resumen["global"]
    assert resumen["global"]["hit_at_1"] == 1.0


def test_leer_preguntas_con_filtros(tmp_path):
    escribir_csv(tmp_path / "e.csv", COLUMNAS, [
        ["1", "pais", "p1", "r", "t", "pais_NOR.txt"],
        ["2", "kpi", "p2", "r", "t", "kpis.txt"],
        ["3", "abstencion", "p3", "r", "t", ""],
    ])
    assert len(ev.leer_preguntas(tmp_path / "e.csv")) == 3
    assert [f["id"] for f in ev.leer_preguntas(tmp_path / "e.csv", ids={"1", "3"})] == ["1", "3"]
    assert [f["id"] for f in ev.leer_preguntas(tmp_path / "e.csv", tipos={"kpi"})] == ["2"]


def test_commit_corpus_y_chunker(tmp_path):
    procedencia = tmp_path / "P.md"
    procedencia.write_text("| Commit | `aa4c813818344b8c` (merge) |\n", encoding="utf-8")
    assert ev.commit_corpus(procedencia) == "aa4c813"
    assert ev.commit_corpus(tmp_path / "no.md") == "desconocido"
    meta = tmp_path / "m.json"
    meta.write_text('{"chunker": "parrafos"}', encoding="utf-8")
    assert ev.chunker_indice(meta) == "parrafos"


def test_parser_valores_por_defecto():
    args = ev.construir_parser().parse_args([])
    assert args.top_k == 3 and args.temperatura == 0.2 and not args.mlflow
    assert args.csv.endswith("preguntas_evaluacion_green.csv")
