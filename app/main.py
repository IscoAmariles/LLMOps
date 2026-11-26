import os
import time
from contextlib import asynccontextmanager

import requests
import mlflow

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from rag import indexar_documentos, recuperar_documentos
from metricas import (
    CONSULTAS,
    TOKENS_ENTRADA,
    TOKENS_SALIDA,
    DURACION_TOTAL,
    DURACION_RAG,
    SIMILITUD_RAG
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MLFLOW_URL = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MODELO = "qwen2.5:1.5b"

# Frase de abstencion (decision D5 del plan de equipo). evaluacion.py y las
# respuestas esperadas 25 a 30 dependen de que se use literalmente.
FRASE_ABSTENCION = "No existe información suficiente en los documentos."

INSTRUCCIONES = f"""
Eres un asistente de datos verdes: respondes preguntas sobre consumo de
energía, participación renovable y estado ambiental de 20 países.

Reglas:
1. Responde SOLO con la información del CONTEXTO. No uses conocimiento propio.
2. Cita entre paréntesis el nombre del documento fuente, por ejemplo (pais_NOR.txt).
3. Si el contexto no respalda la respuesta, responde exactamente:
   "{FRASE_ABSTENCION}"
   Si preguntan por un país que no aparece en el contexto, agrega que ese país
   no está entre los 20 países del dataset.
4. Son datos de laboratorio, no estadísticas oficiales, sin unidad ni año
   documentados. No inventes unidades, años ni conversiones.
5. Copia las cifras tal como aparecen en el contexto (punto decimal, porcentajes
   con un decimal).
6. Responde siempre en español, de forma breve y clara.
"""

mlflow.set_tracking_uri(MLFLOW_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # MLflow puede tardar en iniciar: esperamos a que esté disponible
    for intento in range(20):
        try:
            mlflow.set_experiment("Laboratorio_RAG_Ollama")
            print("MLflow conectado")
            break
        except Exception as error:
            if intento == 19:
                raise
            print("Esperando MLflow:", error)
            time.sleep(2)
    yield


app = FastAPI(
    title="Laboratorio LLMOps",
    description="Ollama + RAG + Observabilidad",
    version="1.0",
    lifespan=lifespan
)


class Pregunta(BaseModel):
    pregunta: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)
    temperatura: float = Field(default=0.2, ge=0, le=2)


@app.get("/")
def inicio():
    return {"mensaje": "Plataforma LLMOps activa"}


@app.get("/health")
def health():
    return {"estado": "ok"}


@app.post("/indexar")
def indexar(chunker: str | None = None):
    """Reindexa documentos/. ``chunker``: caracteres o parrafos (por defecto,
    la variable de entorno CHUNKER o «caracteres»)."""
    try:
        return indexar_documentos(chunker)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@mlflow.trace(name="generar_respuesta_llm")
def generar_respuesta(pregunta, fragmentos, temperatura):
    contexto = "\n\n".join(
        f"Fuente: {item['fuente']}\nContenido: {item['texto']}"
        for item in fragmentos
    )

    instrucciones = INSTRUCCIONES

    prompt = f"""
CONTEXTO:
{contexto}

PREGUNTA:
{pregunta}

RESPUESTA:
"""

    respuesta = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": MODELO,
            "system": instrucciones,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperatura}
        },
        timeout=300
    )
    respuesta.raise_for_status()
    datos = respuesta.json()

    return {
        "respuesta": datos["response"],
        "tokens_entrada": datos.get("prompt_eval_count", 0),
        "tokens_salida": datos.get("eval_count", 0),
        "duracion_ollama": datos.get("total_duration", 0) / 1e9,
        "duracion_generacion": datos.get("eval_duration", 0) / 1e9
    }


@mlflow.trace(name="pipeline_rag")
def ejecutar_rag(datos: Pregunta):
    recuperacion = recuperar_documentos(
        pregunta=datos.pregunta,
        top_k=datos.top_k
    )
    fragmentos = recuperacion["fragmentos"]

    respuesta = generar_respuesta(
        pregunta=datos.pregunta,
        fragmentos=fragmentos,
        temperatura=datos.temperatura
    )

    DURACION_RAG.observe(recuperacion["tiempo_recuperacion"])
    for fragmento in fragmentos:
        SIMILITUD_RAG.observe(fragmento["similitud"])

    TOKENS_ENTRADA.inc(respuesta["tokens_entrada"])
    TOKENS_SALIDA.inc(respuesta["tokens_salida"])

    return {
        "pregunta": datos.pregunta,
        "respuesta": respuesta["respuesta"],
        "top_k": datos.top_k,
        "temperatura": datos.temperatura,
        "modelo": MODELO,
        "tokens_entrada": respuesta["tokens_entrada"],
        "tokens_salida": respuesta["tokens_salida"],
        "duracion_ollama": respuesta["duracion_ollama"],
        "duracion_generacion": respuesta["duracion_generacion"],
        "tiempo_recuperacion": recuperacion["tiempo_recuperacion"],
        "fuentes": fragmentos
    }


@app.post("/preguntar")
def preguntar(datos: Pregunta):
    inicio = time.perf_counter()
    try:
        resultado = ejecutar_rag(datos)
        CONSULTAS.labels(estado="exito").inc()
        return resultado
    except Exception as error:
        CONSULTAS.labels(estado="error").inc()
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        DURACION_TOTAL.observe(time.perf_counter() - inicio)


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
