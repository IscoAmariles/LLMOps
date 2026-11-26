# Propuesta para las decisiones D1–D7

> **PROPUESTA — pendiente de aprobación del Product Owner.** La preparó el Scrum Master con apoyo de Claude Code.
> Las decisiones oficiales se registran en la última columna de [plan-equipo.md §7](plan-equipo.md#7-decisiones-abiertas), que sigue **en blanco a propósito**. Solo se llena cuando el Product Owner decida.

## Resumen

| ID | Propuesta | Estado en el repo (2026-11-25) |
|---|---|---|
| D1 | Confirmar la recomendación | **Aplicada** en el PR #2 |
| D2 | Confirmar la recomendación | **Aplicada** en el corpus |
| D3 | Confirmar la recomendación | **Parcial**: en documentos sí; falta el prompt |
| D4 | Confirmar el fondo y **cambiar la redacción** | **Aplicada**, con un commit de `main` del ETL |
| D5 | Confirmar la recomendación | **Supuesta** en la evaluación; falta el prompt |
| D6 | Confirmar la recomendación | **Aplicada** en el corpus |
| D7 | Ajustar las metas y **corregir una incoherencia** | Sin aplicar: aún no hay mediciones |

Que algo esté aplicado **no significa que esté aprobado**. Se aplicó por la regla del plan de equipo: «si no se decide, se aplica la recomendación».

## Detalle

### D1 — Corpus del laboratorio
- **Propuesta:** los datos verdes reemplazan a TecnoFábrica; el ejemplo queda en `documentos/ejemplo_tecnofabrica/`.
- **Si se cambia:** el Data Engineer reorganiza `documentos/` y hay que reindexar.

### D2 — Idioma de los documentos
- **Propuesta:** español, conservando el nombre original en inglés y los alias.
- **Nota:** en las fichas de Egipto y Estados Unidos se omitió la traducción de la región para no pasar de 500 caracteres; en la de Egipto también se omitió un alias.
- **Si se cambia:** regenerar el corpus y revisar preguntas y respuestas esperadas.

### D3 — Unidad y año
- **Propuesta:** avisar «datos de laboratorio, sin unidad ni año documentados».
- **Estado:** el aviso está en las fichas, la metodología y `kpis.txt` (no en todos sus bloques). El ranking y los resúmenes por región e ingreso no lo llevan. **Falta en el prompt** (LLM Engineer).
- **Si se cambia:** afecta el corpus, el prompt y las respuestas esperadas 4, 5 y 29.

### D4 — Fuente de los datos
- **Texto actual:** «Snapshot de los CSV Gold de la rama `feat/airflow-medallion-alignment`; no `main`…».
- **Redacción propuesta:** «Snapshot de los CSV Gold del commit `aa4c813` del ETL (mismo árbol que `684fba9` de `feat/airflow-medallion-alignment`); en esta versión, no Postgres».
- **Motivo:** el PR #1 del ETL integró esa rama en `main`, así que la prohibición de usar `main` ya no aplica. Después `main` avanzó a `b6148e5`, que agrega documentos de Product Owner; los dos CSV no cambiaron (verificado el 2026-11-25 comparando sus blobs).

### D5 — Abstención
- **Propuesta:** responder «No existe información suficiente en los documentos.» Si el país no está entre los 20, aclararlo además.
- **Estado:** las respuestas esperadas 25 a 30 asumen esta frase. **Falta en el prompt** (LLM Engineer).
- **Límite:** el chequeo automático solo busca «información suficiente» (en la 29, «document»). La aclaración sobre el país se revisa a mano.
- **Si se cambia la frase:** actualizar `respuesta_esperada` y `terminos_clave` de las filas 25 a 30, y el prompt.

### D6 — Agregación
- **Propuesta:** promedio simple de los países, dicho en cada resumen.
- **Si se cambia:** regenerar los resúmenes y revisar las preguntas 19, 21 y 22.

### D7 — Metas de aceptación

El plan del Product Owner pide en abstención «≥ 90 %» y a la vez «como máximo 1 inventada de 6». **No son compatibles**: 5 de 6 es 83 %. Hay que elegir una. Se propone expresar las metas en número de preguntas, que es más claro con una muestra pequeña:

| Indicador | Meta en el plan | Propuesta sobre las 30 preguntas |
|---|---|---|
| Correctas en `pais` | ≥ 90 % | Al menos 9 de 10 |
| Correctas en `kpi`, `ranking` y `comparacion` | ≥ 70 % | Al menos 9 de 12 |
| Correctas en `explicacion` | ≥ 80 % | 2 de 2 |
| Abstención correcta | ≥ 90 % (máx. 1 inventada) | Al menos 5 de 6 (máx. 1 inventada) |
| Fuente esperada entre las 3 recuperadas, en `pais` | ≥ 95 % | 10 de 10 |
| Consultas con `estado="error"` | 0 | 0 |
| Latencia p95 | Después de medir | Después de medir |

Son metas **provisionales**: todavía no se ha medido nada.

## Registro de la decisión del Product Owner

| ID | Confirma / cambia | Comentario | Fecha |
|---|---|---|---|
| D1 | | | |
| D2 | | | |
| D3 | | | |
| D4 | | | |
| D5 | | | |
| D6 | | | |
| D7 | | | |
