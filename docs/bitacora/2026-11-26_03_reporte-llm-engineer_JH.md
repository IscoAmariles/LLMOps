# Bitácora 03 · Reporte de ejecución · LLM Engineer · Evaluación del RAG de datos verdes

**Proyecto:** Laboratorio LLMOps, RAG de datos verdes  
**Fecha:** 2026-11-26  
**Elaborado por:** JH  
**Rol:** LLM Engineer  
**Rama:** `feat/llm-evaluacion` · **PR:** pendiente  
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
| 3. Adaptar el código | Prompt de datos verdes (D3, D5, cita de fuente); `app/evaluacion.py` parametrizado; chunker `parrafos` en `app/fragmentacion.py`; ejemplo TecnoFábrica movido a `datos/ejemplo_tecnofabrica/` | Hecho |
| 4. Indexar y revisar | 27 documentos, 44 fragmentos; las 20 fichas en un fragmento; `datos/indice_meta.json` | Hecho |
| 5. Recuperación | hit@1 0,542, hit@3 0,625; fuente fuera del top 3 en 9 de 24 preguntas | Hecho |
| 6. Línea base | 16/30 correctas (clasificación manual); no cumple las metas D7 propuestas | Hecho |
| 7. Experimentos | A (`top_k`), B (temperatura), C (abstención), D (rendimiento), E (chunker). F descartado por RAM | Hecho |
| 8. Registro en MLflow | 7 runs: `linea_base`, `A_top_k_1`, `A_top_k_5`, `E_parrafos`, `B_temp_0`, `B_temp_0.5`, `B_temp_1` | Hecho |
| 9. Dashboard de Grafana | Provisionado desde `grafana/provisioning/dashboards/` (8 paneles, todos con datos) | Hecho; capturas pendientes |
| 10. Informe | `docs/evidencias.md` reescrito; README actualizado; este reporte | Hecho |

Pruebas: **51 en verde** (las 32 del DE + 19 nuevas).

## 4. Hallazgos

1. **MLflow 3 no deja sitio a Ollama en un equipo de 7 GB.** Arranca ~8 procesos de trabajos en segundo plano y 4 workers web (1,6 GB, 84 % de CPU); Ollama no cargaba el modelo y la consulta expiraba a los 300 s. Con `--workers 1` y `MLFLOW_SERVER_ENABLE_JOB_EXECUTION=false` baja a ~0,5 GB. Se agregó además `OLLAMA_NUM_PARALLEL=1`.
2. **La recuperación es el cuello de botella de calidad.** Los documentos de apoyo genéricos (`metodologia.txt`, `glosario.txt`, `resumen_por_region.txt`) superan en similitud a la ficha o al ranking correcto. Noruega queda 4.ª con `top_k=3` y el modelo responde 35,4 % (promedio de Europa) en vez de 90,9 %.
3. **El modelo copia la cifra más visible** cuando no tiene la fuente correcta, en lugar de abstenerse. La abstención funciona en 4/6 casos y se rompe con temperatura 1 (0/3).
4. **Ni `top_k=5` ni el chunker por párrafos resuelven el problema:** suben hit@3 (0,625 → 0,750) pero el acierto global apenas cambia y aparecen errores nuevos.
5. **Latencia:** frío ~3 min (carga del modelo con RAM escasa); en caliente se estabiliza en ~4 s tras unas 15 consultas. La traza más lenta pasó el 99,6 % del tiempo en generación.

## 5. Decisiones aplicadas

| Tema | Decisión | Origen |
|---|---|---|
| D3 (unidad y año) | El prompt indica «datos de laboratorio, sin unidad ni año documentados» y prohíbe convertir | Recomendación de `plan-equipo.md` §7 |
| D5 (frase de abstención) | «No existe información suficiente en los documentos.» exacta en el prompt y en el chequeo | Recomendación de `plan-equipo.md` §7 |
| D7 (metas) | Se comparan los resultados contra la **propuesta** de `propuesta-decisiones.md`; no se dan por aprobadas | Pendiente del PO |
| Chunker por defecto | Se mantiene `caracteres`; `parrafos` queda como opción | Experimento E |
| Experimento F | Descartado: `qwen2.5:3b` no cabe en 7 GB | Acordado al planificar |

No se llenaron las columnas de decisión D1–D7 ni las tablas de aprobación.

## 6. Para el seguimiento del Scrum Master

- **Bloqueo para la aceptación:** el sistema no alcanza las metas D7 propuestas (16/30). El PO debe decidir si ajusta las metas o si se invierte en mejorar la recuperación (siguiente punto) antes de la demo.
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
- Las metas D7 y el conjunto de evaluación siguen siendo propuesta (PR #3); si cambian, hay que repetir la línea base.
- Todas las mediciones son de un único equipo con 6,9 GB de RAM; los tiempos no son representativos de un equipo de 16 GB.
- La clasificación manual se hizo solo sobre la línea base; los experimentos se comparan con los chequeos automáticos.
