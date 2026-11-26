# Alcance del asistente de datos verdes

> **BORRADOR — pendiente de aprobación del Product Owner.** Lo preparó el Scrum Master con apoyo de Claude Code para no frenar al equipo. No es una decisión tomada.
> Corresponde al paso 2 del [plan del Product Owner](plan-product-owner.md). Es un laboratorio de asignatura.

## Enunciado

Para **analistas de datos ambientales y estudiantes del laboratorio** que necesitan **consultar el consumo de energía, la participación renovable y el estado ambiental de un grupo de países**, el asistente de datos verdes es **un sistema de preguntas y respuestas en español sobre el dataset Gold del ETL Green Data** que **responde apoyado en documentos y muestra cuáles consultó**. A diferencia de **preguntarle a un modelo de lenguaje sin contexto**, **debe abstenerse cuando los documentos no respaldan la respuesta, y cada consulta se puede observar (trazas y métricas)**.

El enunciado describe el comportamiento **esperado**. Todavía no está medido que el asistente lo cumpla.

## Dentro del alcance

- Consultas sobre cualquiera de los 20 países: capital, región, nivel de ingreso, consumo, energía renovable, participación renovable y estado ambiental.
- Consultas por nombre en español o en inglés, por alias o por código ISO3.
- KPIs globales, rankings y comparaciones por región o nivel de ingreso con **promedio simple**.
- Explicación de las reglas: fórmulas, umbrales `Green` / `Moderate` / `Critical` y significado de las columnas.
- Abstención ante lo que el dataset no contiene.
- Trazabilidad: fuentes recuperadas, trazas en MLflow, métricas en Prometheus y dashboard en Grafana.
- Evaluación con las 30 preguntas de referencia y revisión manual de las respuestas.

## Fuera del alcance

- Evolución en el tiempo o preguntas sobre años concretos.
- Unidades de medida y conversiones.
- Emisiones de CO₂.
- Desglose por tipo de energía (solar, eólica, hidráulica, etc.).
- Países distintos de los 20 del dataset.
- Datos que no están en los documentos, como la población.
- Presentar las cifras como estadísticas oficiales o usarlas para decisiones reales.
- Despliegue en producción, autenticación de usuarios y exposición del sistema fuera del equipo local.
- Lectura directa del warehouse Postgres y actualización automática desde el ETL (backlog).

## Supuestos y advertencias

- Son **datos de laboratorio**, sin unidad ni año documentados.
- Los umbrales 0.30 y 0.10 son una regla del laboratorio, no un estándar.
- El repo del ETL no tiene LICENSE y no se han verificado los términos de uso de los datos del World Bank.

## Relación con el Product Owner del ETL

El repo del ETL contiene documentos de Product Owner sobre **ese** proyecto (`Documentacion_ProductOwner_GreenDataETL/`, commit `b6148e5`). Describen como usuario al Analista de Datos Ambiental y piden indicadores ambientales confiables. No cubren el asistente de preguntas y respuestas. De ahí se tomó el usuario objetivo de este borrador.

## Aprobación

| Campo | Valor |
|---|---|
| Estado | Pendiente |
| Aprobado por (Product Owner) | |
| Fecha | |
| Cambios solicitados | |
