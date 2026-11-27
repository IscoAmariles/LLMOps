"""Estrategias de fragmentacion del corpus (sin dependencias externas).

- ``caracteres``: la original de la guia. Ventanas de ``tamano`` caracteres con
  ``solape``; ignora parrafos y puede partir una ficha o una lista a la mitad.
- ``parrafos``: corta en lineas en blanco y empaqueta bloques completos hasta
  ``tamano`` caracteres. Solo si un bloque por si solo supera ``tamano`` se
  recurre al corte por caracteres para ese bloque.
"""
import re

CHUNKERS = ("caracteres", "parrafos")


def dividir_texto(texto, tamano=500, solape=80):
    """Corte por caracteres con solapamiento (comportamiento original)."""
    if tamano <= solape:
        raise ValueError("El tamaño debe superar el solape")
    fragmentos = []
    inicio = 0
    while inicio < len(texto):
        fin = min(inicio + tamano, len(texto))
        fragmentos.append(texto[inicio:fin])
        if fin == len(texto):
            break
        inicio = fin - solape
    return fragmentos


def dividir_parrafos(texto, tamano=500, solape=80):
    """Empaqueta bloques separados por linea en blanco hasta ``tamano``."""
    if tamano <= solape:
        raise ValueError("El tamaño debe superar el solape")
    bloques = [b.strip() for b in re.split(r"\n\s*\n", texto) if b.strip()]
    fragmentos = []
    actual = ""
    for bloque in bloques:
        if len(bloque) > tamano:
            if actual:
                fragmentos.append(actual)
                actual = ""
            fragmentos.extend(dividir_texto(bloque, tamano, solape))
            continue
        candidato = f"{actual}\n\n{bloque}" if actual else bloque
        if len(candidato) <= tamano:
            actual = candidato
        else:
            fragmentos.append(actual)
            actual = bloque
    if actual:
        fragmentos.append(actual)
    return fragmentos


def fragmentar(texto, chunker="caracteres", tamano=500, solape=80):
    if chunker == "caracteres":
        return dividir_texto(texto, tamano, solape)
    if chunker == "parrafos":
        return dividir_parrafos(texto, tamano, solape)
    raise ValueError(f"Chunker desconocido: {chunker}. Opciones: {CHUNKERS}")
