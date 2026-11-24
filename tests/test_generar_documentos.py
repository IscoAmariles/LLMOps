"""Pruebas de scripts/generar_documentos.py (plan-data-engineer, paso 9)."""
import re

import pytest

import generar_documentos as gen
from conftest import ALIAS, PAISES, escribir_csv


def generar(repo, args_generador):
    assert gen.main(args_generador) == 0
    return {p.name: p.read_text(encoding="utf-8")
            for p in sorted((repo / "documentos").glob("*.txt"))}


def test_una_ficha_por_pais_y_ninguna_supera_500(repo, args_generador):
    docs = generar(repo, args_generador)
    fichas = {n: t for n, t in docs.items() if n.startswith("pais_")}
    assert sorted(fichas) == sorted(f"pais_{p[1]}.txt" for p in PAISES)
    for nombre, texto in fichas.items():
        assert len(texto) <= 500, nombre


def test_cantidad_de_documentos(repo, args_generador):
    docs = generar(repo, args_generador)
    assert len(docs) == len(PAISES) + 7  # con 20 paises: 27


def test_ningun_bloque_supera_500_y_todos_tienen_titulo(repo, args_generador):
    for nombre, texto in generar(repo, args_generador).items():
        for bloque in texto.strip().split("\n\n"):
            assert len(bloque) <= 500, nombre
            assert bloque.split("\n")[0].endswith("."), (nombre, bloque[:60])


def test_ficha_usa_valores_del_gold(repo, args_generador):
    noruega = generar(repo, args_generador)["pais_NOR.txt"]
    assert "Ficha de país: Noruega (Norway), código NOR." in noruega
    assert "Consumo de energía: 220." in noruega
    assert "Energía renovable: 200." in noruega
    assert "90.9 % (Renewable_Share = 0.909)" in noruega
    assert "Green (verde" in noruega
    assert "sin unidad ni año documentados" in noruega


def test_empate_argentina_brasil(repo, args_generador):
    ranking = generar(repo, args_generador)["ranking_participacion_renovable.txt"]
    pos_arg = ranking.index("Argentina (ARG): 9.0 %")
    pos_bra = ranking.index("Brasil (BRA): 9.0 %")
    assert pos_arg < pos_bra  # desempate por Country_Code
    assert "Empate con Brasil" in ranking
    assert "Empate con Argentina" in ranking
    assert "los empates se ordenan por código" in ranking


def test_frontera_exacta_010_es_moderate(repo, args_generador):
    docs = generar(repo, args_generador)
    assert "Estado ambiental: Moderate" in docs["pais_CHN.txt"]
    bloque_moderate = next(b for b in docs["kpis.txt"].split("\n\n")
                           if b.startswith("Países en estado Moderate"))
    assert "China (CHN): 10.0 %" in bloque_moderate


def test_formato_decimal(repo, args_generador):
    for nombre, texto in generar(repo, args_generador).items():
        # Ningun numero con coma decimal (p. ej. "90,9")
        assert not re.search(r"\d,\d", texto), nombre
        # Todo porcentaje con exactamente un decimal y espacio antes de %
        for pct in re.findall(r"\d+(?:\.\d+)? ?%", texto):
            if pct.strip() in {"30 %", "10 %"}:  # umbrales de la regla
                continue
            assert re.fullmatch(r"\d+\.\d %", pct), (nombre, pct)


def test_idempotente(repo, args_generador):
    gen.main(args_generador)
    primera = {p.name: p.read_bytes()
               for p in (repo / "documentos").glob("*.txt")}
    marcas = {p.name: p.stat().st_mtime_ns
              for p in (repo / "documentos").glob("*.txt")}
    gen.main(args_generador)
    segunda = {p.name: p.read_bytes()
               for p in (repo / "documentos").glob("*.txt")}
    assert primera == segunda
    # Sin cambios no se reescribe ningun archivo
    assert marcas == {p.name: p.stat().st_mtime_ns
                      for p in (repo / "documentos").glob("*.txt")}


def test_utf8_y_saltos_lf(repo, args_generador):
    generar(repo, args_generador)
    for ruta in (repo / "documentos").glob("*.txt"):
        datos = ruta.read_bytes()
        assert b"\r\n" not in datos, ruta.name
        datos.decode("utf-8")


def test_falla_si_falta_un_pais_en_alias(repo, args_generador):
    escribir_csv(repo / "datos" / "alias_paises.csv",
                 ["Country_Code", "nombre_es", "nombre_en", "alias"], ALIAS[:-1])
    with pytest.raises(AssertionError, match="NOR"):
        gen.main(args_generador)


def test_falla_si_nombre_en_no_coincide(repo, args_generador):
    alias = [list(a) for a in ALIAS]
    alias[3][2] = "Egypt"  # el Gold dice "Egypt, Arab Rep."
    escribir_csv(repo / "datos" / "alias_paises.csv",
                 ["Country_Code", "nombre_es", "nombre_en", "alias"], alias)
    with pytest.raises(AssertionError, match="EGY"):
        gen.main(args_generador)


def test_ficha_larga_recorta_traduccion_y_alias_pero_no_numeros():
    pais = {
        "codigo": "EGY", "nombre_en": "Egypt, Arab Rep.", "nombre_es": "Egipto",
        "capital": "Cairo",
        "region": "Middle East, North Africa, Afghanistan & Pakistan",
        "ingreso": "Lower middle income", "consumo": 1234.56,
        "renovable": 98.76, "razon": 12.37, "participacion": 0.08,
        "estado": "Critical",
        "alias": ["Egypt", "República Árabe de Egipto", "Egipto (país)",
                  "Arab Republic of Egypt", "Misr"],
    }
    ficha = gen.ficha_pais(pais)
    assert len(ficha) <= 500
    assert "1234.56" in ficha and "98.76" in ficha and "8.0 %" in ficha


def test_ficha_imposible_falla():
    pais = {
        "codigo": "XXX", "nombre_en": "X" * 300, "nombre_es": "Y" * 200,
        "capital": "Z", "region": "R", "ingreso": "High income",
        "consumo": 1, "renovable": 0, "razon": 1, "participacion": 0,
        "estado": "Critical", "alias": [],
    }
    with pytest.raises(AssertionError, match="XXX"):
        gen.ficha_pais(pais)


def test_resumen_regional_usa_promedio_simple(repo, args_generador):
    regiones = generar(repo, args_generador)["resumen_por_region.txt"]
    bloque = next(b for b in regiones.split("\n\n")
                  if "Latin America & Caribbean" in b.split("\n")[0])
    # ARG y BRA: (0.09 + 0.09) / 2 = 9.0 %
    assert "promedio simple de los países): 9.0 %" in bloque
    assert "Cantidad de países: 2." in bloque


def test_limitaciones_lista_los_paises_del_gold(repo, args_generador):
    texto = generar(repo, args_generador)["limitaciones.txt"]
    assert "Solo hay 5 países: Argentina, Brasil, China, Egipto y Noruega." in texto
