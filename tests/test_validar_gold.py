"""Pruebas de scripts/validar_gold.py."""
import validar_gold as vg
from conftest import COLUMNAS, PAISES, escribir_csv, filas_gold, filas_kpis


def ejecutar(repo, filas_esperadas=len(PAISES)):
    fuente = repo / "datos" / "fuente"
    informe = vg.controles(fuente / "gold_final.csv", fuente / "kpis.csv",
                           filas_esperadas)
    return {codigo: estado for codigo, estado, _, _ in informe.resultados}


def test_datos_correctos_pasan_los_10_controles(repo):
    resultado = ejecutar(repo)
    assert resultado == {f"C{i}": "PASS" for i in range(1, 11)}


def test_frontera_010_cuenta_como_moderate():
    assert vg.clasificar(0.10) == "Moderate"
    assert vg.clasificar(0.30) == "Green"
    assert vg.clasificar(0.0999) == "Critical"


def test_estado_mal_clasificado_falla_c9(repo):
    filas = filas_gold()
    filas[2][-1] = "Critical"  # China en 0.10 debe ser Moderate
    escribir_csv(repo / "datos" / "fuente" / "gold_final.csv", COLUMNAS, filas)
    assert ejecutar(repo)["C9"] == "FAIL"


def test_codigo_repetido_falla_c3(repo):
    filas = filas_gold()
    filas[1][1] = "ARG"
    escribir_csv(repo / "datos" / "fuente" / "gold_final.csv", COLUMNAS, filas)
    assert ejecutar(repo)["C3"] == "FAIL"


def test_columnas_en_otro_orden_falla_c1(repo):
    columnas = COLUMNAS[1:] + COLUMNAS[:1]
    filas = [f[1:] + f[:1] for f in filas_gold()]
    escribir_csv(repo / "datos" / "fuente" / "gold_final.csv", columnas, filas)
    assert ejecutar(repo)["C1"] == "FAIL"


def test_cantidad_de_filas_distinta_falla_c2(repo):
    assert ejecutar(repo, filas_esperadas=20)["C2"] == "FAIL"


def test_renovable_mayor_que_consumo_falla_c6(repo):
    filas = filas_gold()
    filas[4][8] = 300  # Noruega: renovable 300 > consumo 220
    escribir_csv(repo / "datos" / "fuente" / "gold_final.csv", COLUMNAS, filas)
    assert ejecutar(repo)["C6"] == "FAIL"


def test_celda_vacia_falla_c4(repo):
    filas = filas_gold()
    filas[0][2] = ""
    escribir_csv(repo / "datos" / "fuente" / "gold_final.csv", COLUMNAS, filas)
    assert ejecutar(repo)["C4"] == "FAIL"


def test_kpi_distinto_falla_c10(repo):
    kpis = filas_kpis()
    kpis[1][1] = 999
    escribir_csv(repo / "datos" / "fuente" / "kpis.csv", ["kpi", "value"], kpis)
    assert ejecutar(repo)["C10"] == "FAIL"


def test_kpis_en_formato_ancho(repo):
    kpis = filas_kpis()
    escribir_csv(repo / "datos" / "fuente" / "kpis.csv",
                 [k for k, _ in kpis], [[v for _, v in kpis]])
    assert ejecutar(repo)["C10"] == "PASS"


def test_main_devuelve_1_si_falla(repo):
    fuente = str(repo / "datos" / "fuente")
    assert vg.main(["--fuente", fuente, "--filas-esperadas", "5"]) == 0
    assert vg.main(["--fuente", fuente, "--filas-esperadas", "20"]) == 1
