"""Genera el corpus de datos verdes (plan-data-engineer, paso 6).

Lee datos/fuente/gold_final.csv, datos/fuente/kpis.csv y
datos/alias_paises.csv, y escribe en documentos/ los 27 archivos .txt que
indexa el RAG: 20 fichas de pais y 7 documentos de apoyo.

Uso, desde la raiz del repo:

    python scripts/generar_documentos.py

Reglas que garantiza:
- Idempotente: dos ejecuciones seguidas producen los mismos bytes.
- Ninguna ficha de pais ni ningun bloque supera 500 caracteres.
- Falla si un pais del Gold no esta en la tabla de alias (o al reves).
- Orden determinista por Country_Code y desempate explicito en el texto.
- Punto decimal y porcentajes con un decimal ("90.9 %").
- UTF-8 con saltos de linea LF.

Ningun numero se escribe a mano: todos salen de datos/fuente/.
Solo biblioteca estandar.
"""
import argparse
import csv
import sys
from collections import OrderedDict
from pathlib import Path

from validar_gold import clave_kpi

LIMITE = 500
UMBRAL_GREEN = 0.30
UMBRAL_MODERATE = 0.10
NOTA = ("Nota: datos de laboratorio, no estadísticas oficiales; "
        "sin unidad ni año documentados.")

REGIONES_ES = {
    "Latin America & Caribbean": "América Latina y el Caribe",
    "Europe & Central Asia": "Europa y Asia Central",
    "East Asia & Pacific": "Asia Oriental y el Pacífico",
    "North America": "América del Norte",
    "Sub-Saharan Africa": "África subsahariana",
    "South Asia": "Asia meridional",
    "Middle East, North Africa, Afghanistan & Pakistan":
        "Oriente Medio, Norte de África, Afganistán y Pakistán",
    "Middle East & North Africa": "Oriente Medio y Norte de África",
}
INGRESOS_ES = {
    "High income": "ingreso alto",
    "Upper middle income": "ingreso mediano alto",
    "Lower middle income": "ingreso mediano bajo",
    "Low income": "ingreso bajo",
}
KPIS_ES = {
    "total_paises": "Total de países",
    "consumo_promedio": "Consumo de energía promedio",
    "consumo_maximo": "Consumo de energía máximo",
    "consumo_minimo": "Consumo de energía mínimo",
    "renovable_promedio": "Energía renovable promedio",
    "cantidad_green": "Cantidad de países en estado Green (verde)",
    "cantidad_critical": "Cantidad de países en estado Critical (crítico)",
}
ESTADOS = ["Green", "Moderate", "Critical"]
ESTADOS_ES = {
    "Green": "verde",
    "Moderate": "moderado",
    "Critical": "crítico",
    "Unknown": "desconocido",
}
ESTADOS_REGLA = {
    "Green": "verde: participación renovable ≥ 30 %",
    "Moderate": "moderado: participación renovable ≥ 10 % y < 30 %",
    "Critical": "crítico: participación renovable < 10 %",
    "Unknown": "desconocido: sin dato de participación",
}


# ---------------------------------------------------------------------------
# Formato
# ---------------------------------------------------------------------------

def fmt_num(valor):
    """Punto decimal, sin ceros sobrantes: 220 -> '220', 152.5 -> '152.5'."""
    redondeado = round(valor, 2)
    if redondeado == int(redondeado):
        return str(int(redondeado))
    return f"{redondeado:.2f}".rstrip("0").rstrip(".")


def fmt_pct(participacion):
    """0.909 -> '90.9 %' (un decimal, punto decimal)."""
    return f"{participacion * 100:.1f} %"


def pct_redondeado(participacion):
    """Clave de orden: la participacion tal como se muestra (un decimal)."""
    return round(participacion * 100, 1)


def region_es(region):
    return REGIONES_ES.get(region, region)


def ingreso_es(ingreso):
    return INGRESOS_ES.get(ingreso, ingreso)


def estado_txt(estado):
    return f"{estado} ({ESTADOS_ES.get(estado, estado)})"


# ---------------------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------------------

def leer_csv(ruta):
    with Path(ruta).open(encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        return list(lector.fieldnames or []), list(lector)


def leer_gold(ruta):
    _, filas = leer_csv(ruta)
    paises = []
    for f in filas:
        paises.append({
            "codigo": f["Country_Code"].strip(),
            "nombre_en": f["Country"].strip(),
            "capital": f["Capital_City"].strip(),
            "region": f["Region"].strip(),
            "ingreso": f["Income_Level"].strip(),
            "consumo": float(f["Energy_Consumption"]),
            "renovable": float(f["Renewable_Energy"]),
            "razon": float(f["Energy_per_Renewable_Unit"]),
            "participacion": float(f["Renewable_Share"]),
            "estado": f["Environmental_Status"].strip(),
        })
    return sorted(paises, key=lambda p: p["codigo"])


def leer_alias(ruta):
    _, filas = leer_csv(ruta)
    alias = {}
    for f in filas:
        codigo = f["Country_Code"].strip()
        if codigo in alias:
            raise ValueError(f"alias_paises.csv: {codigo} repetido")
        alias[codigo] = {
            "nombre_es": f["nombre_es"].strip(),
            "nombre_en": f["nombre_en"].strip(),
            "alias": [a.strip() for a in (f.get("alias") or "").split("|") if a.strip()],
        }
    return alias


def leer_kpis(ruta):
    """Lista ordenada de (nombre, valor) tal como viene en kpis.csv."""
    columnas, filas = leer_csv(ruta)
    if len(filas) == 1 and len(columnas) > 2:
        return [(c, float(filas[0][c])) for c in columnas]
    col_nombre, col_valor = columnas[0], columnas[1]
    return [(f[col_nombre].strip(), float(f[col_valor])) for f in filas]


def cruzar_alias(paises, alias):
    codigos_gold = {p["codigo"] for p in paises}
    faltan = sorted(codigos_gold - set(alias))
    sobran = sorted(set(alias) - codigos_gold)
    if faltan or sobran:
        raise AssertionError(
            f"alias_paises.csv no cuadra con el Gold. Faltan: {faltan}. "
            f"Sobran: {sobran}."
        )
    for p in paises:
        a = alias[p["codigo"]]
        if a["nombre_en"] != p["nombre_en"]:
            raise AssertionError(
                f"{p['codigo']}: nombre_en {a['nombre_en']!r} no coincide "
                f"con Country {p['nombre_en']!r}"
            )
        p["nombre_es"] = a["nombre_es"]
        p["alias"] = a["alias"]


def nombre(p):
    return f"{p['nombre_es']} ({p['codigo']})"


# ---------------------------------------------------------------------------
# Documentos
# ---------------------------------------------------------------------------

def alias_extra(p):
    """Alias que no repiten el nombre en espanol, en ingles ni el codigo."""
    ya = {p["nombre_es"], p["nombre_en"], p["codigo"]}
    vistos = []
    for a in p["alias"]:
        if a not in ya and a not in vistos:
            vistos.append(a)
    return vistos


def ficha_pais(p):
    """Ficha de un pais en un solo fragmento (<= 500 caracteres).

    Si no cabe, se recorta primero la traduccion de la region, luego los
    alias extra; nunca los numeros.
    """
    extra = alias_extra(p)

    def armar(con_region_es, cant_alias):
        nombre_en = (f" ({p['nombre_en']})"
                     if p["nombre_en"] != p["nombre_es"] else "")
        tambien = (f" También conocido como: {', '.join(extra[:cant_alias])}."
                   if cant_alias else "")
        region = p["region"]
        if con_region_es and region_es(region) != region:
            region = f"{region} ({region_es(region)})"
        lineas = [
            f"Ficha de país: {p['nombre_es']}{nombre_en}, "
            f"código {p['codigo']}.{tambien}",
            f"Capital: {p['capital'].rstrip('.')}. Región: {region}. "
            f"Nivel de ingreso: {p['ingreso']} ({ingreso_es(p['ingreso'])}).",
            f"Consumo de energía: {fmt_num(p['consumo'])}. "
            f"Energía renovable: {fmt_num(p['renovable'])}. "
            f"Participación renovable: {fmt_pct(p['participacion'])} "
            f"(Renewable_Share = {p['participacion']:.3f}).",
            f"Estado ambiental: {p['estado']} "
            f"({ESTADOS_REGLA.get(p['estado'], p['estado'])}).",
            NOTA,
        ]
        return "\n".join(lineas) + "\n"

    total_alias = len(extra)
    # Orden: con region traducida y todos los alias; luego sin traduccion
    # de region; luego quitando alias.
    intentos = [(True, total_alias), (False, total_alias)]
    intentos += [(False, n) for n in range(total_alias - 1, -1, -1)]
    for con_region_es, cant_alias in intentos:
        texto = armar(con_region_es, cant_alias)
        if len(texto) <= LIMITE:
            return texto
    raise AssertionError(
        f"La ficha de {p['codigo']} supera {LIMITE} caracteres aun recortada "
        f"({len(texto)})"
    )


def unir_bloques(bloques):
    return "\n\n".join(b.strip() for b in bloques) + "\n"


def lista_paises(paises):
    return ", ".join(f"{nombre(p)}: {fmt_pct(p['participacion'])}" for p in paises)


def doc_kpis(paises, kpis):
    bloques = []
    lineas = [f"KPIs del dataset de datos verdes ({len(paises)} países)."]
    for nombre_kpi, valor in kpis:
        etiqueta = KPIS_ES.get(clave_kpi(nombre_kpi), nombre_kpi)
        lineas.append(f"- {etiqueta}: {fmt_num(valor)}")
    lineas.append("Los promedios son promedios simples de los países. " + NOTA)
    bloques.append("\n".join(lineas))

    mayor = max(paises, key=lambda p: (p["consumo"], p["codigo"]))
    menor = min(paises, key=lambda p: (p["consumo"], p["codigo"]))
    empatados_max = [p for p in paises if p["consumo"] == mayor["consumo"]]
    empatados_min = [p for p in paises if p["consumo"] == menor["consumo"]]
    bloques.append("\n".join([
        "Países con mayor y menor consumo de energía.",
        "Mayor consumo: "
        + ", ".join(nombre(p) for p in empatados_max)
        + f", con {fmt_num(mayor['consumo'])}"
        + (" (empate)." if len(empatados_max) > 1 else "."),
        "Menor consumo: "
        + ", ".join(nombre(p) for p in empatados_min)
        + f", con {fmt_num(menor['consumo'])}"
        + (" (empate)." if len(empatados_min) > 1 else "."),
        NOTA,
    ]))

    for estado in ESTADOS:
        grupo = [p for p in paises if p["estado"] == estado]
        bloques.append("\n".join([
            f"Países en estado {estado} ({ESTADOS_REGLA[estado]}): "
            f"{len(grupo)}.",
            (lista_paises(grupo) + ".") if grupo else "Ninguno.",
        ]))
    return unir_bloques(bloques)


def ordenar_por_participacion(paises):
    return sorted(paises, key=lambda p: (-pct_redondeado(p["participacion"]), p["codigo"]))


def doc_ranking(paises):
    orden = ordenar_por_participacion(paises)
    bloques = []
    for inicio in range(0, len(orden), 5):
        tramo = orden[inicio:inicio + 5]
        fin = inicio + len(tramo)
        lineas = []
        hay_empate = False
        for puesto, p in enumerate(tramo, start=inicio + 1):
            linea = (f"{puesto}. {nombre(p)}: {fmt_pct(p['participacion'])}, "
                     f"{estado_txt(p['estado'])}.")
            empatados = [o for o in orden if o is not p
                         and pct_redondeado(o["participacion"]) == pct_redondeado(p["participacion"])]
            if empatados:
                hay_empate = True
                linea += " Empate con " + ", ".join(o["nombre_es"] for o in empatados) + "."
            lineas.append(linea)
        titulo = (f"Ranking de participación renovable, puestos {inicio + 1} "
                  f"a {fin} (de mayor a menor"
                  + ("; los empates se ordenan por código" if hay_empate else "")
                  + ").")
        bloques.append("\n".join([titulo, *lineas]))
    return unir_bloques(bloques)


def bloque_grupo(titulo, grupo):
    promedio = sum(p["participacion"] for p in grupo) / len(grupo)
    conteo = ", ".join(
        f"{estado_txt(e)}: {sum(1 for p in grupo if p['estado'] == e)}"
        for e in ESTADOS
    )
    return "\n".join([
        titulo,
        f"Cantidad de países: {len(grupo)}. Países: "
        + ", ".join(nombre(p) for p in grupo) + ".",
        f"Participación renovable promedio (promedio simple de los países): "
        f"{fmt_pct(promedio)}.",
        f"Países por estado: {conteo}.",
    ])


def agrupar(paises, campo):
    grupos = OrderedDict()
    for p in sorted(paises, key=lambda p: (p[campo], p["codigo"])):
        grupos.setdefault(p[campo], []).append(p)
    return grupos


def doc_regiones(paises):
    return unir_bloques(
        bloque_grupo(f"Resumen de la región {r} ({region_es(r)}).", grupo)
        for r, grupo in agrupar(paises, "region").items()
    )


def doc_ingresos(paises):
    return unir_bloques(
        bloque_grupo(f"Resumen del nivel de ingreso {i} ({ingreso_es(i)}).", grupo)
        for i, grupo in agrupar(paises, "ingreso").items()
    )


def doc_metodologia():
    return unir_bloques([
        "Metodología: participación renovable (Renewable_Share).\n"
        "Renewable_Share = Renewable_Energy / Energy_Consumption. Es un valor "
        "entre 0 y 1; en los documentos se muestra como porcentaje con un "
        "decimal (por ejemplo 0.909 = 90.9 %).",
        "Metodología: energía por unidad renovable (Energy_per_Renewable_Unit).\n"
        "Energy_per_Renewable_Unit = Energy_Consumption / (Renewable_Energy + 1). "
        "Se suma 1 al denominador para evitar dividir por cero cuando un país "
        "no tiene energía renovable. NO mide emisiones de CO2: es solo una "
        "razón entre consumo y renovable. En versiones antiguas del ETL esta "
        "columna se llamaba Emission_Efficiency.",
        "Metodología: estado ambiental (Environmental_Status).\n"
        f"Green (verde) si Renewable_Share ≥ {UMBRAL_GREEN:.2f}; Moderate "
        f"(moderado) si ≥ {UMBRAL_MODERATE:.2f} y < {UMBRAL_GREEN:.2f}; "
        f"Critical (crítico) si < {UMBRAL_MODERATE:.2f}; Unknown "
        "(desconocido) si no hay dato. Un valor justo en el umbral cuenta en "
        "el estado superior (exactamente 0.10 es Moderate).",
        "Metodología: aclaraciones.\n"
        "Los umbrales 0.30 y 0.10 son una regla de este laboratorio, no un "
        "estándar internacional. Los resúmenes por región y por nivel de "
        "ingreso usan el promedio simple de los países, sin ponderar. " + NOTA,
    ])


def doc_glosario():
    entradas = [
        ("Country", "nombre del país en inglés, tal como lo da el World Bank "
         "(por ejemplo Egypt, Arab Rep.). Los nombres en español están en "
         "cada ficha."),
        ("Country_Code", "código ISO3 del país (por ejemplo COL, NOR). Es la "
         "clave única del dataset."),
        ("Capital_City", "capital del país, en inglés y sin tildes."),
        ("Region", "región del World Bank a la que pertenece el país."),
        ("Income_Level", "nivel de ingreso del World Bank: High income "
         "(alto), Upper middle income (mediano alto), Lower middle income "
         "(mediano bajo)."),
        ("Longitude y Latitude", "coordenadas de la capital."),
        ("Energy_Consumption", "consumo de energía del país. Sin unidad ni "
         "año documentados."),
        ("Renewable_Energy", "energía renovable del país, presumiblemente en "
         "la misma unidad que el consumo (no documentado)."),
        ("Energy_per_Renewable_Unit", "Energy_Consumption / "
         "(Renewable_Energy + 1). No mide emisiones."),
        ("Renewable_Share", "participación renovable: Renewable_Energy / "
         "Energy_Consumption, entre 0 y 1."),
        ("Environmental_Status", "estado ambiental según la participación "
         "renovable: Green (verde), Moderate (moderado), Critical (crítico) "
         "o Unknown (desconocido)."),
    ]
    return unir_bloques(f"Glosario: {c}.\n{c}: {d}" for c, d in entradas)


def doc_limitaciones(paises):
    nombres = sorted(p["nombre_es"] for p in paises)
    lista = ", ".join(nombres[:-1]) + " y " + nombres[-1]
    return unir_bloques([
        "Limitaciones: tiempo y unidades.\n"
        "El dataset no tiene año ni evolución en el tiempo, y no documenta la "
        "unidad de medida de la energía. No se pueden responder preguntas "
        "sobre tendencias, años concretos ni conversiones de unidades.",
        "Limitaciones: emisiones y tipos de energía.\n"
        "El dataset no contiene emisiones de CO2 ni desglose por tipo de "
        "energía (solar, eólica, hidráulica, etc.). Energy_per_Renewable_Unit "
        "no es una medida de emisiones.",
        "Limitaciones: cobertura.\n"
        f"Solo hay {len(paises)} países: {lista}. "
        "Cualquier otro país no está en el dataset.",
        "Limitaciones: origen.\n"
        "Son datos de laboratorio generados por un ETL de práctica, no "
        "estadísticas oficiales. Los umbrales de estado ambiental son una "
        "regla del laboratorio.",
    ])


def generar(paises, kpis):
    """Devuelve {nombre_archivo: contenido} con los documentos."""
    documentos = OrderedDict()
    for p in paises:
        documentos[f"pais_{p['codigo']}.txt"] = ficha_pais(p)
    documentos["kpis.txt"] = doc_kpis(paises, kpis)
    documentos["ranking_participacion_renovable.txt"] = doc_ranking(paises)
    documentos["resumen_por_region.txt"] = doc_regiones(paises)
    documentos["resumen_por_nivel_ingreso.txt"] = doc_ingresos(paises)
    documentos["metodologia.txt"] = doc_metodologia()
    documentos["glosario.txt"] = doc_glosario()
    documentos["limitaciones.txt"] = doc_limitaciones(paises)
    return documentos


def verificar(documentos, paises):
    for nombre_doc, texto in documentos.items():
        if nombre_doc.startswith("pais_"):
            assert len(texto) <= LIMITE, f"{nombre_doc}: {len(texto)} caracteres"
        for numero, bloque in enumerate(texto.split("\n\n"), start=1):
            assert len(bloque) <= LIMITE, (
                f"{nombre_doc}, bloque {numero}: {len(bloque)} caracteres"
            )
    esperados = len(paises) + 7
    assert len(documentos) == esperados, (
        f"se generaron {len(documentos)} documentos, se esperaban {esperados}"
    )


def escribir(documentos, salida):
    salida.mkdir(parents=True, exist_ok=True)
    cambiados = []
    for nombre_doc, texto in documentos.items():
        ruta = salida / nombre_doc
        datos = texto.encode("utf-8")
        if not ruta.exists() or ruta.read_bytes() != datos:
            ruta.write_bytes(datos)
            cambiados.append(nombre_doc)
    return cambiados


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fuente", default="datos/fuente", type=Path)
    parser.add_argument("--alias", default="datos/alias_paises.csv", type=Path)
    parser.add_argument("--salida", default="documentos", type=Path)
    args = parser.parse_args(argv)

    paises = leer_gold(args.fuente / "gold_final.csv")
    cruzar_alias(paises, leer_alias(args.alias))
    kpis = leer_kpis(args.fuente / "kpis.csv")
    documentos = generar(paises, kpis)
    verificar(documentos, paises)
    cambiados = escribir(documentos, args.salida)

    print(f"{len(documentos)} documentos generados en {args.salida}/ "
          f"({len(cambiados)} con cambios)")
    otros = sorted(p.name for p in args.salida.glob("*.txt")
                   if p.name not in documentos)
    if otros:
        print("Aviso: hay otros .txt en la carpeta que tambien se indexarian: "
              + ", ".join(otros))
    return 0


if __name__ == "__main__":
    sys.exit(main())
