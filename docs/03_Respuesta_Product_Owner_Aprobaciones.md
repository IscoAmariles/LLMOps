# Respuesta del Product Owner
## Aprobación de preguntas, decisiones, historias de usuario, alcance y entrega de Data Engineering

**Proyecto:** Green Data RAG sobre plataforma LLMOps

**Rol:** Product Owner

**Fecha:** 23/11/2026

---

# Objetivo

Dar respuesta formal a los puntos pendientes identificados por el equipo relacionados con:

- Banco de preguntas.
- Política de abstención.
- Decisiones D1–D7.
- Historias de Usuario HU-01 a HU-07.
- Alcance funcional.
- Aceptación de la entrega del Data Engineer.

---

# 1. Banco de Preguntas

## Consulta

¿Las preguntas registradas en `datos/banco_preguntas.csv` representan lo que debe responder el asistente?

## Decisión

✅ APROBADO

El banco de preguntas representa adecuadamente el comportamiento esperado del asistente y constituye la referencia funcional para la construcción y evaluación del sistema RAG.

Se confirma que dichas preguntas deben ser utilizadas como base para:

- Construcción del conjunto de evaluación.
- Validación funcional.
- Criterios de aceptación.
- Demostración final del producto.

---

## Prioridad 1

### Consulta

¿Se aprueban las 12 preguntas clasificadas como Prioridad 1?

### Decisión

✅ APROBADO

Se consideran adecuadas siempre que cubran los siguientes escenarios:

1. Consulta de datos por país.
2. Consulta de Renewable Share.
3. Consulta de Environmental Status.
4. Consulta de consumo energético.
5. Comparación entre países.
6. Ranking.
7. Indicadores globales.
8. Información regional.
9. Nivel de ingreso.
10. Explicación de clasificación ambiental.
11. Recuperación de fuentes.
12. Casos de abstención.

No se requieren cambios adicionales.

---

# 2. Política de Abstención

## Consulta

Cuando el sistema no encuentre información suficiente en el contexto recuperado.

## Decisión

✅ APROBADO

La respuesta oficial del sistema será:

> No existe información suficiente en los documentos.

---

## País fuera del dataset

### Decisión

✅ APROBADO

Si un usuario consulta un país que no se encuentra dentro de los 20 países disponibles en el dataset, el sistema deberá responder:

> El país consultado no se encuentra incluido en el dataset utilizado por este asistente.

Esta respuesta complementa la política general de abstención y evita alucinaciones.

No se solicitan modificaciones adicionales.

---

# 3. Decisiones D1–D7

## D1 - Corpus del laboratorio

### Decisión

✅ APROBADA

Se reemplaza definitivamente el corpus TecnoFábrica por el corpus Green Data.

El contenido de ejemplo se conservará únicamente como material de referencia y no participará en la indexación.

**Fecha:** 23/11/2026

---

## D2 - Idioma de los documentos

### Decisión

✅ APROBADA

Los documentos deberán generarse en español.

Se conservará:

- Nombre oficial original del país.
- Alias utilizados por los usuarios.
- Variantes en inglés y español.

**Fecha:** 23/11/2026

---

## D3 - Unidad y año de los datos

### Decisión

✅ APROBADA

Toda documentación, respuestas y prompts deberán indicar explícitamente:

> Los datos utilizados corresponden a información de laboratorio y no poseen unidad de medida ni año documentado.

**Fecha:** 23/11/2026

---

## D4 - Fuente oficial del proyecto

### Decisión

✅ APROBADA

La única fuente válida para esta versión del proyecto será:

`feat/airflow-medallion-alignment`

No deberá utilizarse información proveniente de la rama:

`main`

**Fecha:** 23/11/2026

---

## D5 - Política de abstención

### Decisión

✅ APROBADA

Se adopta formalmente la política:

> No existe información suficiente en los documentos.

Para países fuera del dataset:

> El país consultado no se encuentra incluido en el dataset utilizado por este asistente.

**Fecha:** 23/11/2026

---

## D6 - Método de agregación

### Decisión

✅ APROBADA

Las métricas agregadas deberán calcularse utilizando promedio simple sobre el conjunto de países disponible.

Toda respuesta agregada deberá explicitar este criterio.

**Fecha:** 23/11/2026

---

## D7 - Metas de aceptación

### Decisión

✅ APROBADA CON AJUSTE

Se establecen las siguientes metas de aceptación:

| Métrica | Objetivo |
|----------|-----------|
| Precisión de respuestas | ≥ 85 % |
| Recuperación correcta de fuentes | ≥ 90 % |
| Abstenciones correctas | 100 % |
| Alucinaciones verificadas | 0 |
| Registro en MLflow | 100 % |
| Métricas Prometheus | 100 % |
| Dashboard Grafana operativo | 100 % |

Estas metas sustituyen las provisionales y serán utilizadas durante la aceptación final.

**Fecha:** 23/11/2026

---

# 4. Historias de Usuario HU-01 a HU-07

## Resultado

✅ TODAS APROBADAS

### HU-01

Consultar información detallada de un país.

✅ Aprobada

---

### HU-02

Consultar indicadores globales del dataset.

✅ Aprobada

---

### HU-03

Comparar dos o más países.

✅ Aprobada

---

### HU-04

Consultar rankings y posiciones.

✅ Aprobada

---

### HU-05

Visualizar fuentes documentales utilizadas para responder.

✅ Aprobada

---

### HU-06

Abstenerse cuando la información no exista en el corpus.

✅ Aprobada

---

### HU-07

Registrar métricas, trazas y evidencias de ejecución.

✅ Aprobada

---

# 5. Alcance del Proyecto

## Documento

`docs/alcance.md`

## Decisión

✅ APROBADO

Se considera correcto el alcance propuesto.

### Incluye

- Sistema RAG.
- Corpus Green Data.
- Recuperación documental.
- Trazabilidad.
- MLflow.
- Prometheus.
- Grafana.
- Evaluación reproducible.
- Evidencias de desempeño.

### No incluye

- Entrenamiento de modelos.
- Fine-tuning.
- Nuevas fuentes de datos.
- Nuevos países.
- Datos históricos.
- Información externa al corpus.

---

# 6. Entrega del Data Engineer

## Estado de revisión

Se revisaron los entregables asociados a:

- Snapshot de datos.
- Procedencia.
- Contrato de datos.
- Alias de países.
- Corpus documental.
- Conjunto de evaluación.

## Decisión

✅ ACEPTADO

La entrega cumple los requisitos definidos para permitir la construcción y evaluación del sistema RAG.

Se autoriza al equipo de LLM Engineering continuar con:

- Indexación.
- Recuperación documental.
- Evaluación automática.
- Experimentos.
- Generación de evidencias.

Observación:

Las observaciones menores registradas en la revisión del PR #2 podrán cerrarse durante la fase de estabilización, sin bloquear la continuidad del proyecto.

---

# Concepto Final del Product Owner

✅ APROBADO

Se aprueban:

- Banco de preguntas.
- Política de abstención.
- Decisiones D1–D7.
- Historias HU-01 a HU-07.
- Alcance del proyecto.
- Entrega del Data Engineer.

El proyecto queda autorizado para continuar a la fase de construcción, evaluación y aceptación final.

---

**Andrés Fernando López Rendón**

**Product Owner**

**Green Data RAG - LLMOps**