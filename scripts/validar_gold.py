"""Controles de calidad del snapshot Gold (plan-data-engineer, paso 4).

Lee datos/fuente/gold_final.csv y datos/fuente/kpis.csv, imprime PASS o
FAIL por control y termina con codigo 1 si algun control falla.

Uso, desde la raiz del repo:

    python scripts/validar_gold.py
    python scripts/validar_gold.py --fuente otra/carpeta --filas-esperadas 20

Solo biblioteca estandar. El contrato que implementa esta en
docs/contrato-datos.md.
"""
import argparse
import csv
import math
import re
import sys
import unicodedata
from pathlib import Path

COLUMNAS = [
    "Country",
    "Country_Code",
    "Capital_City",
    "Region",
    "Income_Level",
    "Longitude",
    "Latitude",
    "Energy_Consumption",
    "Renewable_Energy",
    "Energy_per_Renewable_Unit",
    "Renewable_Share",
    "Environmental_Status",
]
FILAS_ESPERADAS = 20
UMBRAL_GREEN = 0.30
UMBRAL_MODERATE = 0.10

# Tolerancias: los CSV pueden traer valores redondeados (p. ej. 0.09 en vez
# de 0.0909...). Un redondeo a 2 decimales desvia como maximo 0.005.
TOL_PARTICIPACION = 0.006
TOL_RELATIVA = 0.01

# Nombres de KPI -> clave interna. Se comparan sin tildes, en minusculas y
# solo con letras y numeros, buscando que TODAS las palabras esten presentes.
PATRONES_KPI = [
    # Primero los conteos por estado, para que "green_countries_count" no
    # se confunda con el total de paises.
    ("cantidad_green", [("green",), ("verde",)]),
    ("cantidad_critical", [("critical",), ("critic",)]),
    ("total_paises", [("total", "countr"), ("total", "pais"), ("count", "countr")]),
    ("consumo_promedio", [("avg", "consum"), ("average", "consum"), ("mean", "consum"), ("promedio", "consum")]),
    ("consumo_maximo", [("max", "consum")]),
    ("consumo_minimo", [("min", "consum")]),
    ("renovable_promedio", [("avg", "renew"), ("average", "renew"), ("mean", "renew"), ("promedio", "renov")]),
]


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", texto.lower()).strip()


def clasificar(participacion):
    if participacion >= UMBRAL_GREEN:
        return "Green"
    if participacion >= UMBRAL_MODERATE:
        return "Moderate"
    return "Critical"


def leer_csv(ruta):
    with Path(ruta).open(encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        return list(lector.fieldnames or []), list(lector)


def clave_kpi(nombre):
    norm = normalizar(nombre)
    for clave, alternativas in PATRONES_KPI:
        for palabras in alternativas:
            if all(p in norm for p in palabras):
                return clave
    return None


def leer_kpis(ruta):
    """Devuelve {nombre_original: valor_float}.

    Acepta formato largo (una fila por KPI: nombre, valor) o ancho (una sola
    fila con una columna por KPI).
    """
    columnas, filas = leer_csv(ruta)
    if len(filas) == 1 and len(columnas) > 2:
        return {c: float(filas[0][c]) for c in columnas}
    if len(columnas) < 2:
        raise ValueError(f"{ruta}: se esperaban al menos 2 columnas")
    nombre, valor = columnas[0], columnas[1]
    return {fila[nombre]: float(fila[valor]) for fila in filas}


def numero(fila, columna):
    return float(fila[columna])


class Informe:
    def __init__(self):
        self.resultados = []

    def registrar(self, codigo, descripcion, errores):
        estado = "PASS" if not errores else "FAIL"
        self.resultados.append((codigo, estado, descripcion, errores))
        print(f"{estado}  {codigo}  {descripcion}")
        for error in errores[:20]:
            print(f"        - {error}")
        if len(errores) > 20:
            print(f"        ... y {len(errores) - 20} mas")

    @property
    def fallos(self):
        return [r for r in self.resultados if r[1] == "FAIL"]


def controles(ruta_gold, ruta_kpis, filas_esperadas=FILAS_ESPERADAS):
    informe = Informe()
    columnas, filas = leer_csv(ruta_gold)

    # C1
    errores = []
    if columnas != COLUMNAS:
        faltan = [c for c in COLUMNAS if c not in columnas]
        sobran = [c for c in columnas if c not in COLUMNAS]
        if faltan:
            errores.append(f"faltan columnas: {faltan}")
        if sobran:
            errores.append(f"columnas inesperadas: {sobran}")
        if not faltan and not sobran:
            errores.append(f"orden distinto: {columnas}")
    informe.registrar("C1", "12 columnas con nombre y orden esperados", errores)
    if any(c not in columnas for c in COLUMNAS):
        print("No se pueden ejecutar los demas controles sin las columnas.")
        return informe

    # C2
    errores = []
    if len(filas) != filas_esperadas:
        errores.append(
            f"{len(filas)} filas, se esperaban {filas_esperadas}: "
            "el corpus se genera por fila, avisa al equipo"
        )
    informe.registrar("C2", f"numero de filas = {filas_esperadas}", errores)

    # C3
    errores = []
    codigos = [f["Country_Code"] for f in filas]
    for codigo in codigos:
        if not re.fullmatch(r"[A-Z]{3}", codigo):
            errores.append(f"codigo invalido: {codigo!r}")
    repetidos = sorted({c for c in codigos if codigos.count(c) > 1})
    if repetidos:
        errores.append(f"codigos repetidos: {repetidos}")
    informe.registrar("C3", "Country_Code unico y de 3 letras mayusculas", errores)

    # C4
    errores = [
        f"fila {i} ({f.get('Country_Code')}): {c} vacio"
        for i, f in enumerate(filas, start=2)
        for c in COLUMNAS
        if not (f.get(c) or "").strip()
    ]
    informe.registrar("C4", "ninguna celda vacia", errores)

    # Filas con numeros legibles, para los controles C5-C9
    numericas = []
    errores_c5 = []
    for f in filas:
        cod = f["Country_Code"]
        try:
            consumo = numero(f, "Energy_Consumption")
            renovable = numero(f, "Renewable_Energy")
            participacion = numero(f, "Renewable_Share")
            razon = numero(f, "Energy_per_Renewable_Unit")
        except ValueError as error:
            errores_c5.append(f"{cod}: valor no numerico ({error})")
            continue
        if not consumo > 0:
            errores_c5.append(f"{cod}: Energy_Consumption = {consumo} (debe ser > 0)")
        if not renovable >= 0:
            errores_c5.append(f"{cod}: Renewable_Energy = {renovable} (debe ser >= 0)")
        numericas.append((f, consumo, renovable, participacion, razon))
    informe.registrar("C5", "Energy_Consumption > 0 y Renewable_Energy >= 0, numericos", errores_c5)

    # C6
    errores = [
        f"{f['Country_Code']}: renovable {r} > consumo {c}"
        for f, c, r, _, _ in numericas
        if r > c
    ]
    informe.registrar("C6", "Renewable_Energy <= Energy_Consumption", errores)

    # C7
    errores = []
    for f, c, r, p, _ in numericas:
        if not 0 <= p <= 1:
            errores.append(f"{f['Country_Code']}: Renewable_Share = {p} fuera de [0, 1]")
        elif c > 0 and abs(p - r / c) > TOL_PARTICIPACION:
            errores.append(
                f"{f['Country_Code']}: Renewable_Share = {p}, "
                f"pero Renewable_Energy / Energy_Consumption = {r / c:.4f}"
            )
    informe.registrar("C7", "Renewable_Share en [0, 1] y coherente", errores)

    # C8
    errores = []
    for f, c, r, _, q in numericas:
        esperado = c / (r + 1)
        if not math.isclose(q, esperado, rel_tol=TOL_RELATIVA, abs_tol=0.01):
            errores.append(
                f"{f['Country_Code']}: Energy_per_Renewable_Unit = {q}, "
                f"esperado {esperado:.4f}"
            )
    informe.registrar("C8", "Energy_per_Renewable_Unit = consumo / (renovable + 1)", errores)

    # C9
    errores = []
    for f, c, r, p, _ in numericas:
        esperado = clasificar(p)
        if f["Environmental_Status"] != esperado:
            errores.append(
                f"{f['Country_Code']}: estado {f['Environmental_Status']!r}, "
                f"esperado {esperado!r} (Renewable_Share = {p})"
            )
        elif c > 0 and clasificar(r / c) != esperado:
            errores.append(
                f"{f['Country_Code']}: frontera ambigua, Renewable_Share = {p} "
                f"da {esperado} pero el cociente exacto {r / c:.6f} da "
                f"{clasificar(r / c)}"
            )
    informe.registrar("C9", "Environmental_Status coincide con umbrales 0.30 / 0.10", errores)

    # C10
    errores = []
    try:
        kpis = leer_kpis(ruta_kpis)
    except (OSError, ValueError, KeyError) as error:
        kpis = {}
        errores.append(f"no se pudo leer {ruta_kpis}: {error}")
    if numericas and kpis:
        consumos = [c for _, c, _, _, _ in numericas]
        renovables = [r for _, _, r, _, _ in numericas]
        estados = [f["Environmental_Status"] for f, *_ in numericas]
        calculados = {
            "total_paises": len(filas),
            "consumo_promedio": sum(consumos) / len(consumos),
            "consumo_maximo": max(consumos),
            "consumo_minimo": min(consumos),
            "renovable_promedio": sum(renovables) / len(renovables),
            "cantidad_green": estados.count("Green"),
            "cantidad_critical": estados.count("Critical"),
        }
        vistos = set()
        for nombre, valor in kpis.items():
            clave = clave_kpi(nombre)
            if clave is None:
                errores.append(f"KPI no reconocido: {nombre!r} (ajusta PATRONES_KPI)")
                continue
            vistos.add(clave)
            esperado = calculados[clave]
            if not math.isclose(valor, esperado, rel_tol=1e-3, abs_tol=0.01):
                errores.append(f"{nombre}: kpis.csv dice {valor}, el Gold da {esperado:.4f}")
        for clave in calculados:
            if clave not in vistos:
                errores.append(f"falta el KPI {clave} en kpis.csv")
    informe.registrar("C10", "KPIs coinciden con el Gold", errores)

    return informe


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fuente", default="datos/fuente", type=Path,
                        help="carpeta con gold_final.csv y kpis.csv")
    parser.add_argument("--filas-esperadas", default=FILAS_ESPERADAS, type=int)
    args = parser.parse_args(argv)

    informe = controles(
        args.fuente / "gold_final.csv",
        args.fuente / "kpis.csv",
        args.filas_esperadas,
    )
    total = len(informe.resultados)
    print(f"\n{total - len(informe.fallos)} de {total} controles en PASS")
    return 1 if informe.fallos else 0


if __name__ == "__main__":
    sys.exit(main())
