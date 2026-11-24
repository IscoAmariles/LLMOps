"""Datos minimos compartidos por las pruebas (estilo del ETL: CSV en tmp_path)."""
import csv

import pytest

COLUMNAS = [
    "Country", "Country_Code", "Capital_City", "Region", "Income_Level",
    "Longitude", "Latitude", "Energy_Consumption", "Renewable_Energy",
    "Energy_per_Renewable_Unit", "Renewable_Share", "Environmental_Status",
]

# Cinco paises con los casos dificiles: empate ARG/BRA en 0.09, China justo
# en la frontera 0.10, nombre con coma (Egipto) y un pais Green.
PAISES = [
    # nombre, codigo, capital, region, ingreso, consumo, renovable, share, estado
    ("Argentina", "ARG", "Buenos Aires", "Latin America & Caribbean",
     "Upper middle income", 300, 27, "0.09", "Critical"),
    ("Brazil", "BRA", "Brasilia", "Latin America & Caribbean",
     "Upper middle income", 500, 45, "0.09", "Critical"),
    ("China", "CHN", "Beijing", "East Asia & Pacific",
     "Upper middle income", 1000, 100, "0.1", "Moderate"),
    ("Egypt, Arab Rep.", "EGY", "Cairo",
     "Middle East, North Africa, Afghanistan & Pakistan",
     "Lower middle income", 250, 10, "0.04", "Critical"),
    ("Norway", "NOR", "Oslo", "Europe & Central Asia", "High income",
     220, 200, "0.909", "Green"),
]

ALIAS = [
    ("ARG", "Argentina", "Argentina", ""),
    ("BRA", "Brasil", "Brazil", "Brazil"),
    ("CHN", "China", "China", ""),
    ("EGY", "Egipto", "Egypt, Arab Rep.", "Egypt"),
    ("NOR", "Noruega", "Norway", "Norway"),
]


def escribir_csv(ruta, cabecera, filas):
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(cabecera)
        escritor.writerows(filas)


def filas_gold(paises=PAISES):
    filas = []
    for nombre, cod, cap, reg, ing, consumo, renovable, share, estado in paises:
        filas.append([nombre, cod, cap, reg, ing, "-70.1", "4.6", consumo,
                      renovable, round(consumo / (renovable + 1), 2), share,
                      estado])
    return filas


def filas_kpis(paises=PAISES):
    consumos = [p[5] for p in paises]
    renovables = [p[6] for p in paises]
    estados = [p[8] for p in paises]
    return [
        ["total_countries", len(paises)],
        ["avg_energy_consumption", sum(consumos) / len(consumos)],
        ["max_energy_consumption", max(consumos)],
        ["min_energy_consumption", min(consumos)],
        ["avg_renewable_energy", sum(renovables) / len(renovables)],
        ["green_countries", estados.count("Green")],
        ["critical_countries", estados.count("Critical")],
    ]


@pytest.fixture
def repo(tmp_path):
    """Estructura minima: datos/fuente, datos/alias_paises.csv y documentos/."""
    fuente = tmp_path / "datos" / "fuente"
    fuente.mkdir(parents=True)
    escribir_csv(fuente / "gold_final.csv", COLUMNAS, filas_gold())
    escribir_csv(fuente / "kpis.csv", ["kpi", "value"], filas_kpis())
    escribir_csv(tmp_path / "datos" / "alias_paises.csv",
                 ["Country_Code", "nombre_es", "nombre_en", "alias"], ALIAS)
    return tmp_path


@pytest.fixture
def args_generador(repo):
    """Argumentos de generar_documentos.main apuntando al repo temporal."""
    return [
        "--fuente", str(repo / "datos" / "fuente"),
        "--alias", str(repo / "datos" / "alias_paises.csv"),
        "--salida", str(repo / "documentos"),
    ]
