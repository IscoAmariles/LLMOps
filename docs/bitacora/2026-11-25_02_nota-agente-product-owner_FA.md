# Bitácora 02 · Nota de traspaso para el agente del Product Owner

**Proyecto:** Laboratorio LLMOps, RAG de datos verdes (**laboratorio de asignatura**)  
**Fecha:** 2026-11-25  
**Elaborado por:** FA, con asistencia de Claude Code  
**Rol:** Scrum Master  
**Rama:** `feat/po-preguntas-evaluacion`  
**Destinatario:** el agente de IA que asista al Product Owner, y el Product Owner

> **Lo más importante:** se prepararon **borradores** del trabajo del Product Owner para desbloquear al equipo. **Ninguno está aprobado.** Tu tarea es ayudar al Product Owner a revisarlos y decidir, no darlos por hechos.

## 1. Reglas para el agente

1. **No decidas ni apruebes en nombre del Product Owner.** Sin su instrucción explícita:
   - no llenes la columna «Decisión / fecha» de [plan-equipo.md §7](../plan-equipo.md#7-decisiones-abiertas);
   - no llenes las tablas de aprobación de [alcance.md](../alcance.md) ni de [propuesta-decisiones.md](../propuesta-decisiones.md);
   - no quites las etiquetas BORRADOR o PROPUESTA;
   - no apruebes, comentes como aprobación ni fusiones ningún PR;
   - no marques casillas de aceptación.
2. **No deduzcas aprobación** de que algo esté fusionado, ya aplicado en el corpus o escrito en esta nota.
3. **Pregunta antes de suponer.** Presenta cada decisión con su efecto y espera la respuesta.
4. **Respeta los archivos de otros roles:** `documentos/`, `datos/fuente/`, `datos/alias_paises.csv`, `scripts/` y `tests/` son del Data Engineer; `app/` es del LLM Engineer. Si algo ahí debe cambiar, descríbelo para su dueño.
5. **No ejecutes el proyecto** (Docker, stack, modelos). No hace parte del rol de Product Owner.
6. **El repo es público.** No subas datos personales ni credenciales.
7. El repo del ETL es **solo lectura**.
8. Mantén la proporción de un **laboratorio de asignatura**: no agregues alcance ni procesos de un producto en producción.

## 2. Orden de lectura

1. Esta nota.
2. [plan-product-owner.md](../plan-product-owner.md).
3. [plan-equipo.md](../plan-equipo.md): contexto (§3), roles (§2), seguimiento (§2.2) y decisiones (§7). Léelo junto con la sección 8 de esta nota.
4. [alcance.md](../alcance.md) y [propuesta-decisiones.md](../propuesta-decisiones.md).
5. `datos/banco_preguntas.csv` y `datos/preguntas_evaluacion_green.csv`.
6. [Reporte del Data Engineer](2026-11-24_01_reporte-data-engineer-corpus-green_MJGG.md).

Si el PR de esta rama todavía no está fusionado, estos archivos solo están en la rama `feat/po-preguntas-evaluacion`.

## 3. Qué pasó hasta hoy

| Hito | Resultado |
|---|---|
| Planes por rol | Fusionados en el PR #1 |
| Corpus del Data Engineer | Fusionado en el PR #2. La revisión se apoyó en Claude Code: contrastó las cifras del corpus contra el snapshot sin encontrar errores y dejó observaciones en un comentario del PR. **No ejecutó** sus scripts ni sus 32 pruebas |
| Esta rama | Banco de preguntas, conjunto de evaluación, alcance, propuesta D1–D7, rol de Scrum Master y esta nota |

## 4. Qué se preparó y cuál es su estado

| Archivo | Paso del plan del PO | Estado | Dueño de la aprobación |
|---|---|---|---|
| `datos/banco_preguntas.csv` | 5 | Borrador | Product Owner |
| `datos/preguntas_evaluacion_green.csv` | (paso 8 del Data Engineer) | Propuesta | Data Engineer |
| `docs/alcance.md` | 2 | Borrador | Product Owner |
| `docs/propuesta-decisiones.md` | 3 y 6 | Propuesta | Product Owner |
| `docs/plan-equipo.md` §2.1 y §2.2 | — | Nuevo | Scrum Master |

**Desviación del plan que debes conocer:** el plan dice que el Product Owner no escribe respuestas y que el Data Engineer las deriva del dato. Para desbloquear, aquí se redactaron también las respuestas esperadas. **No las edites desde el rol de PO**: si ves un problema, repórtalo al Data Engineer con el `id`.

## 5. Cómo está construido el banco

30 preguntas. Los `id` son los mismos en los dos CSV.

| Tipo | `id` | Cantidad | Historia | Con prioridad 1 |
|---|---|---|---|---|
| `pais` | 1–10 | 10 | HU-01 | 1, 3 |
| `kpi` | 11–14 | 4 | HU-02 | 11, 12 |
| `ranking` | 15–18 | 4 | HU-03 | 15, 17 |
| `comparacion` | 19–22 | 4 | HU-04 | 19, 20 |
| `explicacion` | 23–24 | 2 | HU-05 | 23, 24 |
| `abstencion` | 25–30 | 6 | HU-06 | 25, 28 |

- Las **12 de prioridad 1** son dos por tipo. Sirven para la prueba de aceptación (paso 8) y para pruebas cortas.
- HU-07 (trazabilidad) no tiene preguntas propias: se comprueba al observar las trazas y métricas de cualquier consulta. El plan pide dos preguntas por historia, así que el Product Owner debe confirmar si acepta esta excepción.
- Las variantes incluyen un alias (id 4, «EE. UU.»), una en inglés (id 3) y una mal escrita (id 8).
- **Cambio frente al ejemplo del plan:** «¿Qué países de América Latina están en estado Critical?» no se responde con un solo documento. La id 20 pregunta **cuántos** son.
- El orden de las historias y su redacción salen de la propuesta del plan (paso 4), que el Product Owner aún no ha confirmado.

## 6. Verificación hecha y no hecha

**Hecho** (script propio que solo lee archivos): los dos CSV coinciden en `id`, `tipo` y `pregunta`; hay 30 filas con la distribución de la tabla; cada `fuente_esperada` existe; los términos clave están en la respuesta esperada; en las filas que no son de abstención, esos términos y las cifras decimales de la respuesta aparecen en la fuente. Resultado: 0 errores.

**No hecho:** no se ejecutó `scripts/validar_evaluacion.py`; no se le hizo ninguna pregunta al modelo; no hay línea base, hit@k ni metas medidas.

## 7. Límites de la evaluación automática

La clasificación final (correcta, incompleta, inventada) es **manual**.

| `id` | Riesgo |
|---|---|
| 5, 11, 14, 20, 23 | Buscan números cortos: pueden aprobar respuestas erróneas |
| 9 | «Asia» también aceptaría «Asia meridional» |
| 18 | No comprueba el orden de los tres países |
| 16 | Falla si el modelo escribe «EE. UU.» en vez de «Estados Unidos» |
| 3, 6 | Aceptan «Moderate» o «moderado»; otras redacciones fallan |
| 23 | También se puede responder con `kpis.txt`, pero solo `metodologia.txt` cuenta como fuente |
| 25–30 | Dependen de que el prompt use la frase de D5. La aclaración de país fuera del dataset (id 25) no se comprueba |
| 22 | Se espera difícil (compara 7 regiones); es una hipótesis sin medir |

## 8. Datos desactualizados en los planes

Estos textos **aún no se han corregido**. Prevalece lo de esta tabla.

| Dónde | Dice | Realidad |
|---|---|---|
| Planes (varias secciones) | El repo ETL es `Laboratorio-MLOps-green-data-etl` | En GitHub se llama `AndreLopezRendon/Laboratorio-Apache-Airflow-`; el nombre anterior redirige |
| plan-equipo §3 (advertencia 1), D4 y plan del Data Engineer (paso 1) | `main` del ETL es una versión antigua; no usarlo | El PR #1 del ETL integró la rama en `main` (`aa4c813`, mismo árbol que `684fba9`). La afirmación salió de revisar solo un clon local atrasado |
| ETL, estado posterior | — | `main` avanzó a `b6148e5`, que agrega documentos de Product Owner. Los dos CSV no cambiaron |
| plan-equipo §8 | El repo no tiene commits | Ya tiene commits y PR fusionados |
| Plan del PO, paso 6 (D7) | Abstención «≥ 90 %» y «máximo 1 inventada de 6» | Son incompatibles (5 de 6 = 83 %). Ver [propuesta D7](../propuesta-decisiones.md#d7--metas-de-aceptación) |

**Sobre los documentos de PO del ETL** (`Documentacion_ProductOwner_GreenDataETL/`: solicitud, propuesta, validación y aceptación): tratan del **ETL**, no del asistente RAG. Sus actas no aceptan nada de este repo. De ellos solo se tomó el usuario objetivo (Analista de Datos Ambiental) para el borrador de alcance.

## 9. Estado de `main` que afecta la aceptación

- El corpus ya es de datos verdes, pero el prompt de `app/main.py` sigue siendo de TecnoFábrica, `app/evaluacion.py` lee el CSV antiguo, y el `README.md` y `evidencias.md` no se han actualizado. Son tareas del LLM Engineer. **La prueba de aceptación no puede hacerse todavía.**
- Al simular el chunker actual sobre el corpus salen 44 fragmentos: las fichas quedan enteras, pero se parten 11 de 38 bloques de los documentos largos. Puede afectar las preguntas de ranking, comparación y explicación.
- Observaciones de la revisión del PR #2 para seguimiento del Data Engineer; las principales: el control C10 puede dar PASS si `kpis.csv` solo tiene la cabecera, y las tolerancias del validador son demasiado amplias. El detalle está en el comentario del PR #2.

## 10. Lo que el agente debe hacer con el Product Owner, en orden

| # | Tarea | Preguntas para el Product Owner | Listo cuando |
|---|---|---|---|
| 1 | Entender el dato (paso 1) | ¿Puede explicar en una frase qué sabe y qué no sabe el asistente? | Lo explica con sus palabras |
| 2 | Revisar el alcance | ¿El usuario y el «fuera de alcance» son correctos? | Aprueba o pide cambios |
| 3 | Decidir D1–D6 | Una por una: ¿confirma o cambia? En D4, ¿acepta la nueva redacción? | Seis decisiones expresas |
| 4 | Decidir D7 | ¿Qué regla de abstención queda? ¿Acepta las metas por número de preguntas? | Metas sin incoherencias |
| 5 | Confirmar HU-01 a HU-07 | ¿Faltan o sobran historias? ¿Acepta la excepción de HU-07? | Historias confirmadas |
| 6 | Revisar el banco | ¿Representan lo que debe responder? ¿Están bien las 12 prioritarias? | Aprueba o lista cambios por `id` |
| 7 | Registrar | Con aprobación expresa: llenar plan-equipo §7, las tablas de aprobación y actualizar §2.2 | Queda comentario o revisión del Product Owner en el PR |
| 8 | Aceptar la entrega del Data Engineer (paso 7) | Aplicar el checklist del plan. El conjunto de evaluación sigue como propuesta | Veredicto del Product Owner |
| 9 | Pasos 8 a 10 | Prueba de aceptación, demo y cierre | Cuando el LLM Engineer entregue el asistente y la línea base |

## 11. Si el Product Owner cambia algo

| Cambio | Qué actualizar y quién |
|---|---|
| Una pregunta | La misma fila (`id`) en `banco_preguntas.csv` (PO) y en `preguntas_evaluacion_green.csv` (Data Engineer) |
| Agregar o quitar preguntas | Ambos CSV, el mínimo por tipo y los denominadores de D7 |
| D1, D2 o D6 | Corpus (Data Engineer), reindexar (LLM Engineer) y revisar respuestas esperadas |
| D3 | Corpus, prompt y filas 4, 5 y 29 |
| D4 | Redacción en plan-equipo; si cambia la fuente, snapshot y corpus (Data Engineer) |
| D5 | Filas 25 a 30 y prompt (LLM Engineer) |
| D7 | Plan del PO (paso 6) y plan-equipo §7 |

## 12. Qué reportar al Scrum Master

Al terminar cada sesión, entrega: decisiones tomadas (con fecha), cambios pedidos por `id` o por decisión, dudas abiertas y quién quedó desbloqueado o bloqueado.
