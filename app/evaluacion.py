"""Ejecuta las preguntas de referencia contra la API y guarda la evidencia.

Uso (desde la raiz del proyecto, con la API levantada):

    python app/evaluacion.py

Este script solo recopila evidencia en datos/resultados.json; no calcula
automaticamente la exactitud semantica. Hay que contrastar cada respuesta con
las politicas originales y clasificarla como correcta, incompleta o inventada.
"""
import csv
import json
import time
from pathlib import Path

import requests

API_URL = "http://localhost:8000/preguntar"
RUTA_PREGUNTAS = Path("datos/preguntas_evaluacion.csv")
RUTA_RESULTADOS = Path("datos/resultados.json")

resultados = []

with RUTA_PREGUNTAS.open(encoding="utf-8", newline="") as archivo:
    for fila in csv.DictReader(archivo):
        inicio = time.perf_counter()
        try:
            respuesta = requests.post(
                API_URL,
                json={
                    "pregunta": fila["pregunta"],
                    "top_k": 3,
                    "temperatura": 0.2
                },
                timeout=360
            )
            respuesta.raise_for_status()
            datos = respuesta.json()
            resultados.append({
                "id": fila["id"],
                "pregunta": fila["pregunta"],
                "esperada": fila["respuesta_esperada"],
                "generada": datos["respuesta"],
                "tokens_entrada": datos["tokens_entrada"],
                "tokens_salida": datos["tokens_salida"],
                "duracion": time.perf_counter() - inicio
            })
            print(f"Pregunta {fila['id']} completada")
        except requests.RequestException as error:
            print(f"Error en pregunta {fila['id']}: {error}")

RUTA_RESULTADOS.write_text(
    json.dumps(resultados, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
print("Evaluacion terminada")
