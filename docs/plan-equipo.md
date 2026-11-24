# Plan de equipo — RAG de «datos verdes»

> Escrito para: el equipo del laboratorio (product owner, data engineer y LLM engineer).
> Léelo completo antes de abrir el plan de tu rol: aquí están el contexto del dataset, los entregables compartidos y las decisiones abiertas.

## 1. Objetivo

Reemplazar el corpus de ejemplo (TecnoFábrica) por el dataset del ETL **Green Data** y dejar funcionando, sobre el stack LLMOps de este repo, un asistente que responde **en español** sobre 20 países (consumo de energía, participación renovable y estado ambiental), con trazabilidad completa: fuentes recuperadas, tokens, latencias y trazas en MLflow, métricas en Prometheus y dashboard en Grafana.

El resultado no es solo "que responda", sino poder **demostrar con evidencia** cuándo responde bien, cuándo se equivoca y cuándo debe negarse a contestar.

## 2. Planes por rol

| Rol | Plan | Entrega principal |
|---|---|---|
| Product Owner | [plan-product-owner.md](plan-product-owner.md) | Alcance, decisiones, banco de preguntas y criterios de aceptación |
| Data Engineer | [plan-data-engineer.md](plan-data-engineer.md) | Snapshot de datos validado y corpus de documentos listo para indexar |
| LLM Engineer | [plan-llm-engineer.md](plan-llm-engineer.md) | RAG adaptado, evaluación reproducible y experimentos |

## 3. Contexto del dataset

**Origen (solo lectura):** `C:\GitProjects\Laboratorio-MLOps-green-data-etl`, un ETL con arquitectura Medallion (Bronze → Silver → Gold → Data Warehouse) orquestado con Airflow. Une el CSV `data/energy_consumption.csv` (20 países, datos de laboratorio) con metadatos de países de la API del World Bank.

**Qué usamos:** la capa **Gold**: `data/gold/gold_final.csv` (20 filas × 12 columnas, una fila por país) y `reports/kpis.csv` (7 KPIs).

**Cifras observadas** al preparar este plan, en la rama `feat/airflow-medallion-alignment`, commit `684fba9`. Verifícalas contra los CSV antes de usarlas; no las copies a mano a ningún documento.

### Esquema de `gold_final.csv`

| Columna | Significado |
|---|---|
| `Country` | Nombre en inglés tal como lo da el World Bank (p. ej. `Egypt, Arab Rep.`) |
| `Country_Code` | ISO3, clave única (`COL`, `NOR`…) |
| `Capital_City` | Capital en inglés y sin tildes |
| `Region` | 7 valores en el dataset: Latin America & Caribbean (7 países), Europe & Central Asia (4), East Asia & Pacific (3), North America (2), Sub-Saharan Africa (2), South Asia (1), Middle East, North Africa, Afghanistan & Pakistan (1) |
| `Income_Level` | High income (10), Upper middle income (7), Lower middle income (3) |
| `Longitude`, `Latitude` | Coordenadas de la capital |
| `Energy_Consumption` | Consumo de energía. **Sin unidad ni año documentados** |
| `Renewable_Energy` | Energía renovable, en la misma unidad (suposición razonable, no documentada) |
| `Energy_per_Renewable_Unit` | `Energy_Consumption / (Renewable_Energy + 1)`. No mide emisiones |
| `Renewable_Share` | `Renewable_Energy / Energy_Consumption`, entre 0 y 1 |
| `Environmental_Status` | `Green` si `Renewable_Share ≥ 0.30`; `Moderate` si `≥ 0.10`; `Critical` si `< 0.10`; `Unknown` si no hay dato |

Distribución actual: 6 `Green`, 5 `Moderate`, 9 `Critical`, 0 `Unknown`. KPIs: total de países, consumo promedio / máximo / mínimo, energía renovable promedio, cantidad de `Green` y de `Critical`.

### Lo que el dataset NO contiene (y el asistente debe reconocer)

- Evolución en el tiempo (no hay año).
- Unidad de medida de la energía.
- Emisiones de CO₂ (la columna `Energy_per_Renewable_Unit` se llamaba `Emission_Efficiency` en versiones anteriores, pero es solo una razón entre consumo y renovable: no mide emisiones).
- Desglose por tipo de energía (solar, eólica…).
- Países distintos de los 20.
- Texto narrativo: es un dataset **puramente tabular**. Hay que construir los documentos de texto para el RAG.

### Advertencias

1. **Rama correcta.** La rama `main` del repo ETL es una versión antigua: 5 países, columna `Emission_Efficiency` y otra regla de clasificación (Colombia aparece como `Critical` en `main` y como `Moderate` en la rama actual). Usa siempre `feat/airflow-medallion-alignment`.
2. **No son estadísticas oficiales.** El propio ETL lo declara: datos de laboratorio. El asistente nunca debe presentarlos como cifras oficiales.
3. **Los umbrales 0.30 / 0.10 son una regla del laboratorio**, no un estándar.
4. **Fronteras y empates.** China tiene exactamente `0.10` (cuenta como `Moderate`). Argentina y Brasil empatan en `0.09`.
5. **Nombres.** Un usuario dirá «Egipto», «EE. UU.» o «Egypt»; el dato dice `Egypt, Arab Rep.` y `United States`.
6. **Licencia.** El repo ETL no tiene LICENSE y no se verificaron los términos de uso de los datos del World Bank.

## 4. Qué cambia en este repo

| Elemento | Hoy | Después | Dueño |
|---|---|---|---|
| `documentos/*.txt` | 3 políticas de TecnoFábrica | 27 documentos de datos verdes; el ejemplo pasa a `documentos/ejemplo_tecnofabrica/` | Data Engineer |
| Prompt del sistema en `app/main.py` | «Eres un asistente de TecnoFabrica…» | Asistente de datos verdes con política de abstención | LLM Engineer |
| `app/evaluacion.py` | Lee un CSV fijo y guarda respuestas | Parametrizado, con chequeos automáticos y registro en MLflow | LLM Engineer |
| `datos/preguntas_evaluacion.csv` | 8 preguntas de TecnoFábrica | `datos/preguntas_evaluacion_green.csv` | Data Engineer (el ejemplo lo mueve LLM Engineer) |
| `docs/evidencias.md` y `README.md` | Hablan de TecnoFábrica | Actualizados al nuevo corpus | LLM Engineer (aceptación: PO) |

El stack (Docker Compose con Ollama, API, MLflow, Prometheus y Grafana) **no cambia**.

## 5. Entregables compartidos y traspasos

| Artefacto | Ruta | Produce | Consume |
|---|---|---|---|
| Decisiones D1–D7 | [sección 7](#7-decisiones-abiertas) | Product Owner | Todos |
| Banco de preguntas | `datos/banco_preguntas.csv` — `id,tipo,pregunta,historia,prioridad` | Product Owner | Data Engineer |
| Snapshot de datos y procedencia | `datos/fuente/gold_final.csv`, `datos/fuente/kpis.csv`, `datos/fuente/PROCEDENCIA.md` | Data Engineer | Data Engineer, LLM Engineer |
| Contrato de datos y controles | `docs/contrato-datos.md`, `scripts/validar_gold.py` | Data Engineer | Todos |
| Alias de países | `datos/alias_paises.csv` | Data Engineer | Data Engineer |
| Corpus indexable (27 `.txt`) | `documentos/` | Data Engineer | LLM Engineer |
| Conjunto de evaluación | `datos/preguntas_evaluacion_green.csv` | Data Engineer | LLM Engineer |
| Resultados de evaluación | `datos/resultados_*.json` (ignorados por Git) y runs en MLflow | LLM Engineer | Product Owner |
| Informe de evidencias | `docs/evidencias.md` | LLM Engineer y PO | Todos |

### Contrato del conjunto de evaluación

`datos/preguntas_evaluacion_green.csv`, UTF-8, separador coma, **con comillas** en los campos que contengan comas:

| Columna | Contenido |
|---|---|
| `id` | El mismo `id` del banco de preguntas |
| `tipo` | `pais`, `kpi`, `ranking`, `comparacion`, `explicacion` o `abstencion` |
| `pregunta` | Texto tal como lo escribió el Product Owner |
| `respuesta_esperada` | Respuesta legible, derivada del dato |
| `terminos_clave` | Cadenas separadas por `|` que deben aparecer en la respuesta (sin distinguir mayúsculas) |
| `fuente_esperada` | Archivo de `documentos/` que debe aparecer entre las `fuentes` recuperadas; vacío en `abstencion` |

Convención de formato en documentos **y** respuestas esperadas, para que la comparación automática funcione: **punto decimal** y porcentajes con **un decimal** (`90.9 %`).

## 6. Orden de ejecución

| Fase | Product Owner | Data Engineer | LLM Engineer |
|---|---|---|---|
| 0. Preparación | Convoca el arranque | Lee su plan | Hace el commit inicial y crea las ramas (ver §8) |
| 1. Alineación (en paralelo) | Decisiones D1–D7, historias y banco de preguntas | Verifica y congela los datos, contrato de datos, alias | Levanta el stack, humo con el corpus de ejemplo, adapta prompt y `evaluacion.py` |
| 2. Corpus | Revisa la primera entrega | Genera los 27 documentos y el conjunto de evaluación | Revisa la entrega y prepara el chunker |
| 3. Evaluación | Atiende dudas | Corrige datos si algo no cuadra | Indexa, mide recuperación, línea base y experimentos |
| 4. Aceptación | Prueba de aceptación, demo y cierre | Soporte | Informe técnico y demo |

Dependencias duras: el Data Engineer necesita **D1, D2, D4 y D6** y el banco de preguntas para cerrar la fase 2; el LLM Engineer necesita **D3 y D5** para el prompt.

## 7. Decisiones abiertas

Las resuelve el Product Owner. **Si no se decide, se aplica la recomendación**, para no bloquear a nadie. Registra la decisión y la fecha en la columna final.

| ID | Decisión | Recomendación | Afecta a | Decisión / fecha |
|---|---|---|---|---|
| D1 | Corpus del laboratorio | Reemplazar TecnoFábrica por datos verdes; el ejemplo pasa a `documentos/ejemplo_tecnofabrica/` (no se indexa porque la lectura de `documentos/` no es recursiva) | DE, LLM | |
| D2 | Idioma de los documentos | Español, conservando el nombre original en inglés y los alias de cada país | DE, LLM | |
| D3 | Cómo presentar unidad y año | Toda ficha, la metodología y el prompt avisan: «datos de laboratorio, sin unidad ni año documentados» | DE, LLM | |
| D4 | Fuente de los datos | Snapshot de los CSV Gold de la rama `feat/airflow-medallion-alignment`; no `main` y, en esta versión, tampoco Postgres | DE | |
| D5 | Política de abstención | Si el contexto no lo respalda: «No existe información suficiente en los documentos.» Para países fuera de los 20: indicar que no está en el dataset | LLM, PO | |
| D6 | Cómo agregar | Promedio simple de los países, dicho explícitamente en cada resumen | DE | |
| D7 | Metas de aceptación | Ver el plan del Product Owner (paso 6); son provisionales y se ajustan tras la primera medición | Todos | |

## 8. Convenciones de trabajo

- **Commit inicial pendiente:** este repo todavía no tiene commits. Antes de crear ramas, el LLM Engineer hace el commit inicial en `main` con lo generado.
- **Ramas** sugeridas: `feat/po-alcance`, `feat/de-corpus-green`, `feat/llm-evaluacion`. Se integran a `main` por pull request.
- **Commits** al estilo del ETL: Conventional Commits en inglés (`feat(corpus): …`, `docs: …`). Documentación y mensajes de usuario en español; nombres de columnas tal como están en el dato.
- **Comandos** en PowerShell, desde la raíz del repo.
- **El repo ETL es solo lectura.** Nadie escribe ni hace commits ahí. Si alguien regenera datos en ese repo, revisa `git status` allí al terminar.
- **Puertos:** este stack usa 11434, 8000, 5000, 9090 y 3000; el ETL con Airflow usa 8080 y 5433. No chocan, pero **no levantes ambos stacks a la vez** con 16 GB de RAM: para este trabajo no necesitas Airflow, solo los CSV.
- **Cuidado con los volúmenes:** nunca `docker compose down -v` si ya descargaste modelos.
