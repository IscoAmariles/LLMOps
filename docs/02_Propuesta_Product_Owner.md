# Propuesta del Product Owner

## Proyecto
Green Data RAG - LLMOps

## Objetivo General

Desarrollar un asistente basado en arquitectura RAG que permita consultar información ambiental proveniente del proyecto Green Data ETL mediante lenguaje natural en español, garantizando trazabilidad, observabilidad y evaluación reproducible.

## Objetivos Específicos

1. Reemplazar el corpus TecnoFábrica por el corpus Green Data.
2. Construir documentos indexables derivados del dataset Gold.
3. Implementar recuperación de contexto mediante RAG.
4. Incorporar política de abstención controlada.
5. Registrar trazas en MLflow.
6. Exponer métricas en Prometheus.
7. Visualizar resultados mediante Grafana.
8. Validar el comportamiento mediante preguntas de evaluación.

## Decisiones Aprobadas

- D1: Reemplazar TecnoFábrica por Green Data.
- D2: Documentación y respuestas en español.
- D3: Informar ausencia de unidad y año.
- D4: Utilizar únicamente la rama feat/airflow-medallion-alignment.
- D5: Aplicar política de abstención.
- D6: Utilizar promedios simples.
- D7: Metas de aceptación basadas en calidad de respuesta y observabilidad.

## Concepto

La iniciativa se considera alineada con los objetivos del laboratorio de LLMOps y se aprueba para ejecución.

**Andrés Fernando López Rendón**

Product Owner
