"""Pruebas de scripts/validar_evaluacion.py."""
import validar_evaluacion as ve
from conftest import escribir_csv

CABECERA = ve.COLUMNAS


def preparar(tmp_path, filas, banco=None):
    docs = tmp_path / "documentos"
    docs.mkdir()
    (docs / "pais_NOR.txt").write_text(
        "Ficha de país: Noruega (Norway). Participación renovable: 90.9 %.\n",
        encoding="utf-8")
    escribir_csv(tmp_path / "eval.csv", CABECERA, filas)
    ruta_banco = None
    if banco is not None:
        ruta_banco = tmp_path / "banco.csv"
        escribir_csv(ruta_banco, ["id", "tipo", "pregunta", "historia", "prioridad"], banco)
    return ve.validar(tmp_path / "eval.csv", docs, ruta_banco)


FILA_OK = ["1", "pais", "¿Participación de Noruega?", "90.9 %", "90.9|noruega", "pais_NOR.txt"]
FILA_ABS = ["2", "abstencion", "¿CO2 de Noruega?",
            "No existe información suficiente en los documentos.",
            "información suficiente", ""]


def test_conjunto_valido(tmp_path):
    assert preparar(tmp_path, [FILA_OK, FILA_ABS]) == []


def test_termino_ausente(tmp_path):
    fila = FILA_OK[:4] + ["91.0"] + FILA_OK[5:]
    errores = preparar(tmp_path, [fila])
    assert any("91.0" in e for e in errores)


def test_fuente_inexistente_e_id_repetido(tmp_path):
    fila = FILA_OK[:5] + ["pais_XXX.txt"]
    errores = preparar(tmp_path, [FILA_OK, fila])
    assert any("repetido" in e for e in errores)
    assert any("pais_XXX.txt" in e for e in errores)


def test_tipo_invalido(tmp_path):
    fila = [FILA_OK[0], "opinion"] + FILA_OK[2:]
    assert any("tipo" in e for e in preparar(tmp_path, [fila]))


def test_cobertura_del_banco(tmp_path):
    banco = [["1", "pais", "¿Participación de Noruega?", "H1", "alta"],
             ["3", "kpi", "¿Cuántos países hay?", "H2", "alta"]]
    errores = preparar(tmp_path, [FILA_OK], banco)
    assert errores == ["banco id 3: sin fila en el conjunto de evaluacion"]
