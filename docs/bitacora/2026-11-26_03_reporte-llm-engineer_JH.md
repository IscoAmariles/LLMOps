# Bitácora 03 · Reporte de ejecución · LLM Engineer · Evaluación del RAG de datos verdes

**Proyecto:** Laboratorio LLMOps, RAG de datos verdes  
**Fecha:** 2026-11-26  
**Elaborado por:** JH  
**Rol:** LLM Engineer  
**Rama:** `feat/llm-evaluacion` · **PR:** [#4](https://github.com/IscoAmariles/LLMOps/pull/4)  
**Plan ejecutado:** [plan-llm-engineer.md](../plan-llm-engineer.md), pasos 1 a 10  
**Resultados detallados:** [evidencias.md](../evidencias.md)

## 1. Objetivo

Adaptar el RAG al corpus de datos verdes, medir la recuperación y las respuestas con el conjunto de evaluación, comparar configuraciones y dejar la evidencia trazable en MLflow, Prometheus, Grafana y `docs/evidencias.md`.

## 2. Método

- Cada corrida de evaluación es un *run* del experimento `Evaluacion_RAG_Green` en MLflow, con parámetros (modelo, `top_k`, temperatura, chunker, commit del corpus) y el JSON de resultados como artefacto. Se cambia una variable por vez.
- Los chequeos automáticos (`acierto_terminos`, `rango_fuente` → hit@1/hit@3) son de primera pasada; la clasificación final de la línea base es manual (correcta, inventada, abstención indebida).
- La lógica nueva (chunkers, chequeos y agregados) está cubierta por pruebas que no necesitan el stack.
- Trabajo preparado con asistencia de Claude Code.

## 3. Resultado por paso del plan

| Paso | Evidencia | Estado |
|---|---|---|
| 1. Levantar el stack y los modelos | 5 servicios `Up`; `qwen2.5:1.5b` y `nomic-embed-text`; `/health` ok; target `llmops_api` UP | Hecho (con ajuste de memoria, §4.1) |
| 2. Prueba de humo | Noruega en frío 135 s / en caliente 18 s; traza `pipeline_rag` completa; contadores `llm_` en `/metrics` | Hecho |
| 3. Adaptar el código | Prompt de datos verdes con las frases D5 aprobadas y nota D3 agregada en código; `app/evaluacion.py` parametrizado; chunker `parrafos` en `app/fragmentacion.py`; ejemplo TecnoFábrica movido a `datos/ejemplo_tecnofabrica/` | Hecho |
| 4. Indexar y revisar | 27 documentos, 44 fragmentos; las 20 fichas en un fragmento; `datos/indice_meta.json` | Hecho |
| 5. Recuperación | hit@1 0,542, hit@3 0,625; fuente fuera del top 3 en 9 de 24 preguntas | Hecho |
| 6. Línea base | 16/30 correctas (clasificación manual); con el prompt de las decisiones aprobadas, 15/30. No cumple las metas D7 oficiales de calidad | Hecho |
| 7. Experimentos | A (`top_k`), B (temperatura), C (abstención), D (rendimiento), E (chunker). F descartado por RAM | Hecho |
| 8. Registro en MLflow | 9 runs válidos: `linea_base`, `A_top_k_1`, `A_top_k_5`, `E_parrafos`, `B_temp_0`, `B_temp_0.5`, `B_temp_1`, `prompt_d7`, `prompt_d7_v2` (más uno marcado como inválido) | Hecho |
| 9. Dashboard de Grafana | Provisionado desde `grafana/provisioning/dashboards/` (8 paneles, todos con datos) | Hecho; capturas pendientes |
| 10. Informe | `docs/evidencias.md` reescrito; README actualizado; este reporte | Hecho |

Pruebas: **52 en verde** (las 32 del DE + 20 nuevas).

## 4. Hallazgos

1. **MLflow 3 no deja sitio a Ollama en un equipo de 7 GB.** Arranca ~8 procesos de trabajos en segundo plano y 4 workers web (1,6 GB, 84 % de CPU); Ollama no cargaba el modelo y la consulta expiraba a los 300 s. Con `--workers 1` y `MLFLOW_SERVER_ENABLE_JOB_EXECUTION=false` baja a ~0,5 GB. Se agregó además `OLLAMA_NUM_PARALLEL=1`.
2. **La recuperación es el cuello de botella de calidad.** Los documentos de apoyo genéricos (`metodologia.txt`, `glosario.txt`, `resumen_por_region.txt`) superan en similitud a la ficha o al ranking correcto. Noruega queda 4.ª con `top_k=3` y el modelo responde 35,4 % (promedio de Europa) en vez de 90,9 %.
3. **El modelo copia la cifra más visible** cuando no tiene la fuente correcta, en lugar de abstenerse. La abstención funciona en 4/6 casos y se rompe con temperatura 1 (0/3).
4. **Ni `top_k=5` ni el chunker por párrafos resuelven el problema:** suben hit@3 (0,625 → 0,750) pero el acierto global apenas cambia y aparecen errores nuevos.
5. **Latencia:** frío ~3 min (carga del modelo con RAM escasa); en caliente se estabiliza en ~4 s tras unas 15 consultas. La traza más lenta pasó el 99,6 % del tiempo en generación.
6. **Más reglas en el prompt empeoran al modelo de 1,5B.** El prompt largo con las decisiones aprobadas bajó a 14/30 e inventó datos de Italia; la lista de países se filtró a los rankings. La versión adoptada mantiene el prompt corto con las frases D5 y agrega la nota D3 en código (100 % de cumplimiento). Queda un falso positivo: Uruguay recibió la frase de país fuera del dataset.

## 5. Decisiones aplicadas

| Tema | Decisión | Origen |
|---|---|---|
| D3 (unidad y año) | La nota aprobada se agrega en código a toda respuesta con cifras; el prompt prohíbe inventar unidades y años | Aprobada por el PO el 23/11/2026 |
| D5 (abstención) | Las dos frases aprobadas, exactas en el prompt; `evaluacion.py` reconoce ambas | Aprobada por el PO el 23/11/2026 |
| D6 (promedio simple) | No se pide al modelo (empeoró la evaluación); los documentos de resumen ya lo indican | Aprobada; cumplimiento parcial, pendiente |
| D7 (metas) | Resultados comparados con las metas oficiales: se cumplen las de observabilidad, no las de calidad | Aprobada con ajuste por el PO |
| Chunker por defecto | Se mantiene `caracteres`; `parrafos` queda como opción | Experimento E |
| Experimento F | Descartado: `qwen2.5:3b` no cabe en 7 GB | Acordado al planificar |

La aprobación del PO llegó a `main` durante la ejecución; la rama se rebasó sobre ella. No se tocaron los documentos del PO.

## 6. Para el seguimiento del Scrum Master

- **Bloqueo para la aceptación:** el sistema no alcanza las metas de calidad de D7 (precisión ~50 % frente a ≥ 85 %; recuperación 65 % frente a ≥ 90 %; abstención 67 % frente a 100 %). El PO debe decidir si revisa las metas o si se invierte en mejorar la recuperación (siguiente punto) antes de la aceptación final.
- **Mejora con más impacto esperado:** priorizar la ficha cuando la pregunta nombra un país (usar `datos/alias_paises.csv` para detectarlo) o recuperación híbrida. Es trabajo del LLM Engineer; se propone como siguiente iteración.
- **Para el DE:** evaluar si `glosario.txt` y `metodologia.txt` deben repetir tanto los términos de las preguntas o indexarse aparte. El alias «EE. UU.» no recupera la ficha de Estados Unidos (pregunta 4).
- **Infraestructura:** el ajuste de memoria del compose es necesario en equipos de 8 GB; el resto del equipo debe hacer `git pull` antes de levantar el stack.
- **Obsoleto en los planes:** el paso «commit inicial» de `plan-llm-engineer.md` (el repo ya tenía historia) y el nombre del repo del ETL (ya señalado en la bitácora 01).

## 7. Cómo reproducir

```powershell
docker compose up -d
docker compose exec ollama ollama pull qwen2.5:1.5b
docker compose exec ollama ollama pull nomic-embed-text
curl.exe -X POST http://localhost:8000/indexar
python app\evaluacion.py datos\preguntas_evaluacion_green.csv --top-k 3 --temperatura 0.2 --mlflow --etiqueta linea_base
```

Los experimentos se repiten cambiando `--top-k`, `--temperatura` (con `--repeticiones 3 --ids 2,8,12,17,19,25`) o reindexando con `?chunker=parrafos`. Los resultados varían ligeramente entre corridas por la temperatura y por el estado de memoria del equipo.

## 8. Pendientes y límites

- Capturas del dashboard y de una traza en `docs/img/` (la sesión de trabajo no tenía navegador).
- Si el PO cambia las metas o el conjunto de evaluación, hay que repetir la corrida `prompt_d7_v2`.
- La pregunta 25 (Italia) tiene como término clave «información suficiente»; con la frase D5 de país fuera del dataset no coincidiría. `evaluacion.py` acepta ambas frases en `abstencion`, pero conviene que el DE actualice la respuesta esperada.
- Todas las mediciones son de un único equipo con 6,9 GB de RAM; los tiempos no son representativos de un equipo de 16 GB.
- La clasificación manual se hizo solo sobre la línea base; los experimentos se comparan con los chequeos automáticos.
