# Evidencias del laboratorio

Resultados del RAG de datos verdes (Green Data, 20 países) medidos el 2026-11-26 por el LLM Engineer (JH). Cada conclusión se apoya en una corrida registrada: los JSON de resultados se generan en `datos/resultados_*.json` (no versionados) y cada corrida de evaluación es un *run* del experimento `Evaluacion_RAG_Green` en MLflow, con el JSON como artefacto.

**Configuración común:** `qwen2.5:1.5b` y `nomic-embed-text` en Ollama (CPU), corpus de 27 documentos (commit del ETL `aa4c813`), conjunto `datos/preguntas_evaluacion_green.csv` de 30 preguntas (propuesta del PR #3; las metas D7 siguen sin aprobación del PO). Equipo: Windows 11, **6,9 GB de RAM**, Docker con 3,5 GB y 8 CPU.

## Checklist

- [x] 1. Cinco servicios con Docker Compose: `ollama`, `mlflow`, `llmops-api`, `prometheus` y `grafana` en `Up`.
- [x] 2. Ollama con `qwen2.5:1.5b` (986 MB) y `nomic-embed-text` (274 MB) (`ollama list`).
- [x] 3. Indexación: `POST /indexar` → 27 documentos, 44 fragmentos (`caracteres`); las 20 fichas `pais_*.txt` quedan en un fragmento cada una (`datos/indice_meta.json`).
- [x] 4. Consulta con fragmentos recuperados (ver *Prueba de humo*).
- [x] 5. Trazas en MLflow (`Laboratorio_RAG_Ollama`): 197 trazas `pipeline_rag` → `recuperar_documentos` + `generar_respuesta_llm`.
- [x] 6. PromQL de tokens, latencia y similitud (las del README) devuelven datos.
- [x] 7. Dashboard `Monitoreo LLMOps: Ollama y RAG` provisionado; los 8 paneles muestran datos. *Capturas pendientes:* la sesión no tenía navegador; se toman a mano y se guardan en `docs/img/`.
- [x] 8. Comparación de `top_k` = 1, 3 y 5 (experimento A).
- [x] 9. Temperatura (B), preguntas sin evidencia (C), rendimiento (D) y fragmentación (E).
- [x] 10. Conclusiones.

## Memoria: el hallazgo que condicionó todo

Con la configuración original, la primera pregunta falló por tiempo de espera (`Read timed out`, 300 s): Ollama no logró cargar el modelo. `docker stats` mostró que **MLflow 3 ocupaba 1,6 GB y 84 % de CPU**, porque arranca unos 8 consumidores de trabajos en segundo plano (`huey`, ~145 MB cada uno) y 4 workers web que este laboratorio no usa.

Cambios en `docker-compose.yml`:

| Ajuste | Efecto |
|---|---|
| MLflow `--workers 1` y `MLFLOW_SERVER_ENABLE_JOB_EXECUTION=false` | MLflow pasa de 1,6 GB a ~0,5 GB en arranque y ~50 MB en reposo |
| Ollama `OLLAMA_NUM_PARALLEL=1` | Reserva contexto para una sola consulta a la vez |

Uso medido con el modelo cargado: Ollama 1,45 GB, Grafana ~0,5 GB, API ~0,1 GB, Prometheus ~0,07 GB y MLflow ~0,05 GB. **El stack funciona en un equipo de 7 GB** si no hay otros contenedores pesados y el navegador está cerrado. Igual queda muy justo: Windows comprime memoria y la latencia en caliente tarda varias consultas en estabilizarse (ver D). El experimento F (`qwen2.5:3b`) se descartó porque no cabe.

## Prueba de humo

Pregunta: «¿Qué participación renovable tiene Noruega?» (`top_k=3`, temperatura 0.2). Dato real: 90,9 % (`pais_NOR.txt`).

| Consulta | Respuesta | `duracion_ollama` | Recuperación | Total |
|---|---|---|---|---|
| En frío | «35.4 %» (incorrecta) | 121,5 s | 10,5 s | 135 s |
| En caliente | «35.4 %» (incorrecta) | 6,6 s | 9,4 s | 18 s |

Fuentes recuperadas: `metodologia.txt` (0,756), `glosario.txt` (0,748), `resumen_por_region.txt` (0,713). La ficha `pais_NOR.txt` queda **cuarta** (0,712): fuera del contexto con `top_k=3`. El modelo copió el promedio de Europa y Asia Central (35,4 %). Con `top_k=5` responde 90,9 %.

## Línea base (`top_k=3`, temperatura 0.2, chunker `caracteres`)

Run MLflow `linea_base`. Clasificación manual de cada respuesta frente a la esperada (C = correcta, I = inventada o incorrecta, A = abstención indebida):

| id | Tipo | Respuesta generada (resumen) | Fuente esperada en top 3 | Clasificación |
|---|---|---|---|---|
| 1 | pais | Noruega 35,4 % | No (4.ª) | I |
| 2 | pais | Capital de Egipto: Cairo | Sí (1.ª) | C |
| 3 | pais | Colombia: Moderate (pregunta en inglés) | Sí (1.ª) | C |
| 4 | pais | «No existe información suficiente…» (EE. UU.) | No | A |
| 5 | pais | Canadá: «participación 25,0 %» (se pedía energía renovable: 200) | Sí (1.ª) | I |
| 6 | pais | China: Moderado | Sí (1.ª) | C |
| 7 | pais | Kenia: Lower middle income | Sí (1.ª) | C |
| 8 | pais | Uruguay 75,0 % (pregunta con errores de tipeo) | Sí (1.ª) | C |
| 9 | pais | Japón: East Asia & Pacific | Sí (1.ª) | C |
| 10 | pais | Alemania 5,4 % | Sí (3.ª) | C |
| 11 | kpi | 6 países en Green | Sí (3.ª) | C |
| 12 | kpi | 568.75 | Sí (1.ª) | C |
| 13 | kpi | «No existe información suficiente…» | No | A |
| 14 | kpi | «1» (son 9 en Critical) | No | I |
| 15 | ranking | Noruega, «con 35,4 %» (cifra errónea) | No | I |
| 16 | ranking | Noruega (es Estados Unidos) | No | I |
| 17 | ranking | China con 3000 | Sí (1.ª) | C |
| 18 | ranking | Noruega 35,4 %, Chile, Argentina (son Noruega, Uruguay, Kenia) | No | I |
| 19 | comparacion | Europa y Asia Central 35,4 % | Sí (1.ª) | C |
| 20 | comparacion | «1» (son 3) | Sí (1.ª) | I |
| 21 | comparacion | Egipto 2,9 % (confunde nivel de ingreso con país) | No | I |
| 22 | comparacion | América Latina 35,4 % (es África subsahariana 37,5 %) | Sí (1.ª) | I |
| 23 | explicacion | «≥ 13,3 %» (es ≥ 10 % y < 30 %) | No | I |
| 24 | explicacion | Renovable / consumo | Sí (1.ª) | C |
| 25 | abstencion | Italia: frase D5 | — | C |
| 26 | abstencion | CO₂ de Alemania: frase D5 | — | C |
| 27 | abstencion | Chile 2015–2020: frase D5 | — | C |
| 28 | abstencion | Noruega solar: «90.9 %» | — | I |
| 29 | abstencion | Unidad del consumo: «unidades de energía consumida» | — | I |
| 30 | abstencion | Población de Colombia: frase D5 | — | C |

### Frente a las metas propuestas (D7, pendientes de aprobación del PO)

| Meta | Obtenido | ¿Cumple? |
|---|---|---|
| País: ≥ 9/10 correctas | 7/10 | No |
| KPI + ranking + comparación: ≥ 9/12 | 4/12 | No |
| Explicación: 2/2 | 1/2 | No |
| Abstención: ≥ 5/6 | 4/6 | No |
| Ficha de país en top 3: 10/10 | 8/10 | No |
| Errores técnicos: 0 | 0 | Sí |

Total: **16/30 correctas**. Chequeo automático de términos: 0,567; hit@1 0,542; hit@3 0,625; p95 50,9 s; 704 tokens de entrada de media.

### Causas de los fallos

1. **Recuperación (causa principal).** `metodologia.txt`, `glosario.txt` y `resumen_por_region.txt` repiten «participación renovable», «Green», «Critical»… y superan en similitud a la ficha o al ranking que de verdad responde. La fuente esperada quedó fuera del top 3 en 9 de las 24 preguntas con fuente; `ranking_participacion_renovable.txt` no entró en ninguna de las 3 preguntas que lo necesitaban.
2. **El modelo copia la cifra más visible del contexto.** El 35,4 % de Europa y Asia Central aparece como dato de Noruega, del ranking y de otra región. Sin la fuente correcta, el modelo de 1,5B rara vez se abstiene: prefiere un número cercano.
3. **Abstención indebida (2 casos).** Cuando la fuente no se recupera, a veces sí aplica la frase D5, aunque el dato exista (EE. UU., promedio de energía renovable).
4. **Abstención fallida (2 casos).** Si el contexto trae un número relacionado (la ficha de Noruega para «¿qué porcentaje es solar?»), responde con ese número.
5. **Lo que sí funciona:** la pregunta en inglés (Colombia), el alias «Egipto» → `Egypt, Arab Rep.` y la pregunta con errores de tipeo (Uruguay) recuperan su ficha en primer lugar. «EE. UU.» no la recupera (id 4). Las fichas de país nunca se parten.

## Experimento A: tamaño del contexto (`top_k`)

Temperatura 0.2, chunker `caracteres`, 30 preguntas. Runs `A_top_k_1`, `linea_base` y `A_top_k_5`.

| Indicador | K = 1 | K = 3 | K = 5 |
|---|---|---|---|
| Acierto de términos (global) | 0,433 | 0,567 | 0,600 |
| Acierto en `pais` | 0,70 | 0,70 | **0,90** |
| Acierto en `kpi` / `comparacion` | 0,00 / 0,00 | 0,50 / 0,25 | 0,50 / 0,25 |
| Acierto en `ranking` | 0,50 | 0,50 | 0,25 |
| hit@k de la fuente esperada | 0,542 | 0,625 | 0,750 |
| Tokens de entrada (media) | 416 | 704 | 1001 |
| Duración media / p95 (s) | 13,1 / 20,1 | 26,6 / 50,9 | 49,3 / 77,7 |

Más contexto mejora las preguntas de país (la ficha entra aunque quede 4.ª o 5.ª), pero cuesta +42 % de tokens y +53 % de p95 frente a K = 3, y empeora ranking: más fragmentos con cifras dan al modelo más números para confundir. **Ninguna K alcanza las metas.** El problema es de ordenamiento, no de cantidad.

## Experimento B: temperatura

`top_k=3`, 6 preguntas que se recuperan bien (ids 2, 8, 12, 17, 19 y 25) × 3 repeticiones. Se eligieron así para aislar el efecto de la temperatura; los aciertos no son comparables con la línea base.

| Temperatura | Acierto de términos | Abstención correcta (Italia, id 25) | Respuestas distintas entre repeticiones |
|---|---|---|---|
| 0 | 1,000 | 3/3 | Solo cambia la redacción (Uruguay) |
| 0.5 | 0,944 | 2/3 | Redacción; una vez intenta responder sobre Italia |
| 1 | 0,833 | **0/3** | Redacción; para Italia llega a inventar «790» |

Las cifras de las preguntas con fuente se mantienen en las tres temperaturas. Lo que se rompe al subirla es la **obediencia a la instrucción de abstención**. Para un asistente de datos, temperatura 0.

## Experimento C: preguntas sin evidencia

En la línea base, 4 de 6 abstenciones correctas, con la frase D5 exacta (Italia, CO₂, serie temporal de Chile, población de Colombia). Fallan las dos donde el contexto trae un número parecido: «¿qué porcentaje de Noruega es solar?» → «90.9 %» y «¿en qué unidad se mide el consumo?» → inventa una unidad en vez de decir que no está documentada (D3). La abstención empeora con la temperatura (B) y con el chunker por párrafos (E, la serie de Chile se inventa).

## Experimento D: rendimiento

Misma pregunta (Uruguay, `top_k=3`, temperatura 0.2). Primero se reinicia el contenedor de Ollama para medir en frío.

| Escenario | n | Total medio (s) | Total p95 (s) | `duracion_ollama` media (s) | Recuperación media (s) | Tokens de salida/s |
|---|---|---|---|---|---|---|
| Frío | 1 | 174,0 | 174,0 | 153,9 | 17,3 | 0,2 |
| Caliente, 1.ª tanda | 1 | 33,2 | 33,2 | 22,9 | 7,6 | 0,6 |
| Caliente | 5 | 11,6 | 16,6 | 7,8 | 1,5 | 3,7 |
| Caliente | 10 | 4,1 | 7,7 | 1,8 | 0,23 | 8,6 |

Arrancar en frío cuesta casi 3 minutos (carga del modelo con RAM escasa). Después, el sistema tarda unas 15 consultas en estabilizarse en ~4 s por respuesta: Windows va descomprimiendo y recuperando páginas de memoria. La recuperación también se ve afectada (17 s → 0,2 s) porque el modelo de embeddings comparte la memoria. **La traza más lenta** registrada en MLflow (308,8 s) es la consulta que expiró al inicio: 307,6 s en `generar_respuesta_llm` frente a 0,32 s en `recuperar_documentos`. El cuello de botella es la generación, no la recuperación.

## Experimento E: fragmentación

`top_k=3`, temperatura 0.2, 30 preguntas. Runs `linea_base` (`caracteres`, 44 fragmentos) y `E_parrafos` (`parrafos`, 46 fragmentos: corta en líneas en blanco y no parte bloques).

| Indicador | `caracteres` | `parrafos` |
|---|---|---|
| Acierto de términos (global) | 0,567 | 0,567 |
| hit@1 / hit@3 | 0,542 / 0,625 | 0,458 / **0,750** |
| Ficha de país en top 3 | 8/10 | 9/10 |
| Tokens de entrada (media) | 704 | 642 |
| Duración p95 (s) | 50,9 | 35,8 |

Con párrafos, la fuente correcta entra más a menudo en el top 3 (arregla Noruega, Canadá, la comparación 20 y la explicación 23) y el contexto es más corto y rápido. Pero introduce regresiones (Kenia «Ingleses», Egipto como mayor participación renovable, serie inventada de Chile) y el acierto global queda igual. **Se mantiene `caracteres` por defecto** hasta tener más evidencia; `parrafos` queda disponible (`?chunker=parrafos` o `CHUNKER=parrafos`).

## Conclusiones

1. **El sistema no cumple las metas D7 propuestas** con `qwen2.5:1.5b` en esta configuración: 16/30 correctas en la línea base. La única meta cumplida es 0 errores técnicos.
2. **El cuello de botella de calidad es la recuperación, no el modelo.** Los documentos de apoyo genéricos (`metodologia`, `glosario`, resúmenes) ganan en similitud a las fichas y al ranking. Subir `top_k` (A) o cambiar el chunker (E) mejoran hit@3, pero no lo resuelven y suben el riesgo de que el modelo copie una cifra equivocada.
3. **Temperatura 0** para producción del laboratorio: misma exactitud y abstención más estable (B).
4. **El cuello de botella de latencia es la generación con poca RAM:** frío ~3 min, caliente estable ~4 s. Con 7 GB el stack solo funciona con el ajuste de MLflow descrito arriba.
5. Una similitud alta (0,70–0,75 en los documentos genéricos) no garantiza que el fragmento sirva: la calidad hay que medirla con el conjunto de evaluación, como aquí.

### Siguientes pasos propuestos (no aplicados)

- **Recuperación:** dar prioridad a la ficha cuando la pregunta nombra un país (detectar el país con `alias_paises.csv` y filtrar o reordenar), o recuperación híbrida (palabra clave + vector). Es el cambio con más impacto esperado.
- **Corpus (DE):** revisar si `glosario.txt` y `metodologia.txt` deben repetir tanto los términos de las preguntas, o separarlos del índice principal.
- **Modelo:** repetir la línea base con un modelo mayor en un equipo con ≥ 16 GB (experimento F pendiente).
- **Metas (PO):** decidir D7 con estos resultados a la vista.
