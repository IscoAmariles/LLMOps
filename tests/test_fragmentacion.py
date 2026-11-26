"""Pruebas de app/fragmentacion.py (chunkers del RAG)."""
from pathlib import Path

import pytest

import fragmentacion as fr

DOCUMENTOS = Path(__file__).resolve().parent.parent / "documentos"


def test_caracteres_conserva_comportamiento_original():
    texto = "a" * 1000
    fragmentos = fr.dividir_texto(texto, tamano=500, solape=80)
    assert [len(f) for f in fragmentos] == [500, 500, 160]
    assert fragmentos[1] == texto[420:920]


def test_texto_corto_un_solo_fragmento():
    assert fr.fragmentar("hola", "caracteres") == ["hola"]
    assert fr.fragmentar("hola", "parrafos") == ["hola"]


def test_parrafos_no_parte_bloques_y_empaqueta():
    bloques = ["A" * 200, "B" * 200, "C" * 200]
    fragmentos = fr.dividir_parrafos("\n\n".join(bloques), tamano=500)
    # A y B caben juntos (200 + 2 + 200); C va solo. Ningun bloque se parte.
    assert fragmentos == [f"{bloques[0]}\n\n{bloques[1]}", bloques[2]]


def test_parrafos_respaldo_por_caracteres_para_bloque_gigante():
    fragmentos = fr.dividir_parrafos("corto\n\n" + "X" * 1200 + "\n\nfinal", tamano=500)
    assert fragmentos[0] == "corto"
    assert fragmentos[-1] == "final"
    assert all(len(f) <= 500 for f in fragmentos)


def test_parrafos_ignora_lineas_en_blanco_con_espacios():
    assert fr.dividir_parrafos("uno\n   \ndos", tamano=5, solape=1) == ["uno", "dos"]


def test_chunker_desconocido():
    with pytest.raises(ValueError):
        fr.fragmentar("x", "tokens")


def test_tamano_menor_que_solape():
    with pytest.raises(ValueError):
        fr.dividir_parrafos("x", tamano=50, solape=80)


@pytest.mark.skipif(not DOCUMENTOS.exists(), reason="sin corpus")
@pytest.mark.parametrize("chunker", fr.CHUNKERS)
def test_corpus_real_fichas_en_un_fragmento(chunker):
    fichas = sorted(DOCUMENTOS.glob("pais_*.txt"))
    assert len(fichas) == 20
    for ficha in fichas:
        assert len(fr.fragmentar(ficha.read_text(encoding="utf-8"), chunker)) == 1, ficha.name


@pytest.mark.skipif(not DOCUMENTOS.exists(), reason="sin corpus")
def test_corpus_real_parrafos_no_corta_bloques():
    """Con parrafos, todo bloque <= 500 caracteres llega entero a algun fragmento."""
    for archivo in sorted(DOCUMENTOS.glob("*.txt")):
        texto = archivo.read_text(encoding="utf-8")
        fragmentos = fr.fragmentar(texto, "parrafos")
        for bloque in (b.strip() for b in texto.split("\n\n") if b.strip()):
            if len(bloque) <= 500:
                assert any(bloque in f for f in fragmentos), archivo.name
