# Plan de trabajo — LLM Engineer

> Escrito para: el LLM Engineer del laboratorio. Contexto, entregables compartidos y decisiones abiertas están en [plan-equipo.md](plan-equipo.md).

## Tu misión

Poner a funcionar el RAG sobre el corpus de datos verdes, **medir** qué tan bien recupera y responde, y dejar la evidencia reproducible para que el Product Owner decida con datos. Eres además quien conoce el stack: levantas, adaptas y operas.

## Antes de empezar

- Lee [plan-equipo.md](plan-equipo.md) completo y el [README del laboratorio](../README.md).
- Tus decisiones son **D3 y D5** (cómo presentar unidad/año y la frase de abstención). Si el Product Owner aún no las cerró, aplica las recomendaciones.
- Requisitos: Docker Desktop, ~16 GB de RAM y Python 3 en el equipo. **No levantes a la vez el stack de Airflow del ETL.**
- Trabaja en tu rama `feat/llm-evaluacion`. El commit inicial en `main` lo haces tú (ver plan-equipo §8).

## Paso a paso

### Paso 1 — Levantar el stack y los modelos

Desde la raíz del repo:

```powershell
docker compose config
docker compose build
docker compose up -d
docker compose ps
docker compose exec ollama ollama pull qwen2.5:1.5b
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama list
```

Comprueba `http://localhost:8000/health` (`{"estado":"ok"}`), que MLflow abre en http://localhost:5000 y que en http://localhost:9090/targets el objetivo `llmops_api` está `UP`.

Para detener sin perder datos: `docker compose down`. **Nunca `-v`** una vez descargados los modelos.

Listo cuando: los cinco contenedores están arriba, ambos modelos aparecen en `ollama list` y el objetivo de Prometheus está `UP`.

### Paso 2 — Prueba de humo con el corpus de ejemplo

Antes de cambiar nada, comprueba que el entorno funciona con lo que ya trae el repo (TecnoFábrica):

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/indexar
$cuerpo = @{ pregunta = "¿Cada cuánto se realiza el mantenimiento preventivo?"; top_k = 3; temperatura = 0.2 } | ConvertTo-Json
$r = Invoke-RestMethod -Uri http://localhost:8000/preguntar -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body ([System.Text.Encoding]::UTF8.GetBytes($cuerpo))
$r.respuesta
$r.fuentes | Select-Object fuente, similitud
```

Si prefieres evitar problemas de codificación en PowerShell, usa Swagger en http://localhost:8000/docs.

Repite la consulta una vez más y compara `duracion_ollama`: la primera incluye la carga del modelo. Anota ambos tiempos como referencia de arranque en frío contra caliente.

Listo cuando: obtienes respuesta con `fuentes`, hay una traza `pipeline_rag` en MLflow y `curl.exe -s http://localhost:8000/metrics | Select-String "llm_"` muestra los contadores en movimiento.

### Paso 3 — Adaptar el código al nuevo dominio

Cambios acotados, en tu rama. Los cambios de código en `app/` se aplican con `docker compose restart api` (la carpeta está montada en el contenedor); solo hace falta `up -d --build api` si cambian dependencias.

**a) Prompt del sistema — `app/main.py`**, variable `instrucciones` dentro de `generar_respuesta`. Hoy dice «Eres un asistente de TecnoFabrica…». Reescríbelo para:

- Ser asistente de datos verdes y responder **solo** con el contexto.
- Citar el nombre del documento fuente.
- Usar la **frase exacta de abstención** (D5) cuando el contexto no respalda la respuesta, y avisar si el país no está entre los 20.
- Recordar que son datos de laboratorio sin unidad ni año (D3), sin convertir unidades.
- Responder en español (un modelo de 1.5 B parámetros puede mezclar idiomas: vigílalo en la evaluación).

**b) Evaluación — `app/evaluacion.py`.** Hoy tiene la ruta del CSV fija y guarda solo la respuesta y los tokens. Pásalo a:

- Argumentos de línea de comandos: ruta del CSV, `--top-k`, `--temperatura` y archivo de salida.
- Guardar por pregunta: `tipo`, `top_k`, `temperatura`, la lista de `fuentes` recuperadas (nombre y similitud), `tiempo_recuperacion` y `duracion`.
- Chequeos automáticos de primera pasada: `acierto_terminos` (todos los `terminos_clave` aparecen en la respuesta, sin distinguir mayúsculas) y `hit_fuente` (`fuente_esperada` está entre las `fuentes`).
- La clasificación final (correcta, incompleta, inventada) sigue siendo **manual**: estos chequeos solo la aceleran.

**c) Fragmentación — `app/rag.py`, función `dividir_texto`.** Hoy corta cada 500 caracteres con 80 de solape, sin respetar párrafos. El Data Engineer entrega bloques separados por una línea en blanco. Evalúa (tras el Paso 5) un chunker que **corte en líneas en blanco y empaquete bloques hasta 500 caracteres**, con el corte por caracteres solo como respaldo. Mantén la firma de la función para no romper nada y valida con una prueba.

**d) Archivos de ejemplo.** Mueve `datos/preguntas_evaluacion.csv` a `datos/ejemplo_tecnofabrica/` (el Data Engineer mueve los `.txt`). Agrega a `.gitignore` la línea `datos/resultados_*.json`.

**e) Textos que mencionan TecnoFábrica.** Actualiza `README.md` y `docs/evidencias.md` cuando el nuevo corpus esté en `main`.

Listo cuando: la API responde con el nuevo prompt (prueba una pregunta y una de abstención) y `evaluacion.py --help` muestra los parámetros.

### Paso 4 — Recibir e indexar el corpus nuevo

Cuando el Data Engineer entregue (rama `feat/de-corpus-green`):

```powershell
git merge feat/de-corpus-green          # o el flujo de pull request del equipo
Invoke-RestMethod -Method Post http://localhost:8000/indexar
```

Esperado: `documentos: 27`. Los fragmentos serán **al menos 27**; si hay más, algún documento se partió.

Inspecciona el índice:

```powershell
$idx = Get-Content datos\indice.json -Raw -Encoding UTF8 | ConvertFrom-Json
$idx.Count                                              # total de fragmentos
$idx | Group-Object fuente | Select-Object Name, Count  # fragmentos por archivo
```

Revisa que **cada `pais_<ISO3>.txt` sea un solo fragmento**. Si alguno se partió, devuélveselo al Data Engineer con el nombre del archivo.

Listo cuando: 27 documentos indexados y fichas de país sin partir.

### Paso 5 — Medir la recuperación (sin juzgar todavía al LLM)

La recuperación es la mitad del sistema: si el documento correcto no llega, el modelo no puede acertar. Con las preguntas de tipo `pais`:

1. Ejecuta cada pregunta y mira `fuentes`: ¿la ficha correcta está **primera**? ¿Entre las 3 primeras?
2. Calcula **hit@1** y **hit@3** con el campo `fuente_esperada`.
3. Mira los fallos: ¿es un problema de idioma (español contra inglés), de nombres (`Egypt, Arab Rep.`), de cantidad de fragmentos o de chunker?
4. Con `kpi`, `ranking` y `comparacion`: ¿llegan `kpis.txt`, los rankings y los resúmenes?

Si hit@3 queda por debajo de la meta del Product Owner, prueba en este orden: mejorar alias y texto de fichas (con el Data Engineer), el chunker del Paso 3c, y subir `top_k`.

Listo cuando: tienes hit@1 y hit@3 por tipo de pregunta y conoces la causa de cada fallo.

### Paso 6 — Línea base de evaluación

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install requests
python app\evaluacion.py datos\preguntas_evaluacion_green.csv --top-k 3 --temperatura 0.2
```

(Ajusta la invocación a los parámetros que definas en el Paso 3b.)

Revisa los resultados contra la rúbrica del Product Owner: por cada respuesta que los chequeos automáticos no den por buena, léela y clasifícala **correcta / incompleta / inventada**. Presta atención especial a:

- Preguntas de `abstencion`: ¿usa la frase de D5 o inventa?
- Países fuera de los 20: ¿reconoce que no están en el dataset?
- Respuestas que mezclan datos de dos fichas.

Listo cuando: cada pregunta tiene veredicto y tienes la tasa de acierto por tipo, para compararla con las metas.

### Paso 7 — Experimentos controlados

Cambia **una variable por vez** y registra los resultados en `docs/evidencias.md`.

| Experimento | Qué varías | Qué observas |
|---|---|---|
| A. Tamaño del contexto | `top_k` = 1, 3 y 5 | Tokens de entrada, duración, acierto y hit@k **por tipo de pregunta** (¿ayuda más contexto en `ranking` y no en `pais`?) |
| B. Temperatura | 0, 0.5 y 1, repitiendo cada pregunta 3 veces en ~6 preguntas | Variabilidad y alucinaciones; la temperatura no mide calidad |
| C. Abstención | Las 6 preguntas de `abstencion` más algunas propias | Si se calla o inventa; cuántas inventadas |
| D. Rendimiento | 1, 5 y 10 consultas seguidas, frío contra caliente | Tokens por segundo, p95, `duracion_ollama` |
| E. Fragmentación | Chunker original contra el de párrafos (Paso 3c) | hit@k y fichas partidas |
| F. Opcional | Un modelo mayor (p. ej. `qwen2.5:3b`) si la RAM lo permite | Aciertos en `kpi` y `ranking` contra latencia; implica cambiar la constante `MODELO` en `app/main.py` |

Listo cuando: cada experimento tiene su tabla con datos reales y una conclusión de una línea.

### Paso 8 — Registrar las evaluaciones en MLflow

Para comparar corridas de forma reproducible (el siguiente paso que sugiere la guía), cada ejecución de `evaluacion.py` debe quedar como un *run* de MLflow en un experimento aparte, p. ej. `Evaluacion_RAG_Green`:

```powershell
pip install "mlflow>=3.0,<4"
```

Con `mlflow.set_tracking_uri("http://localhost:5000")` desde el equipo anfitrión (`localhost:5000` está permitido en la configuración de MLflow del Compose). Registra:

- **Parámetros:** modelo, `top_k`, temperatura, chunker usado, commit del corpus (de `datos/fuente/PROCEDENCIA.md`).
- **Métricas:** acierto de términos clave, hit@k, abstenciones correctas, tokens de entrada medios y duración p95.

Mantén separadas las trazas del servicio (`Laboratorio_RAG_Ollama`) y estos runs de evaluación.

Listo cuando: puedes comparar en la UI de MLflow dos configuraciones lado a lado.

### Paso 9 — Observabilidad: dashboard y alertas visuales

En Grafana (http://localhost:3000, usuario y clave de laboratorio `admin`/`admin`) crea el dashboard `Monitoreo LLMOps: Ollama y RAG` con los seis paneles de la tabla del README. Agrega dos más para este caso:

| Panel | Expresión |
|---|---|
| Latencia p95 | `histogram_quantile(0.95, rate(llm_duracion_segundos_bucket[5m]))` |
| Consultas con error | `llm_consultas_total{estado="error"}` |

Genera tráfico con la evaluación (`rate(...)` necesita varias muestras en la ventana) y toma capturas en `docs/img/`.

Identifica con el Product Owner la consulta más lenta y abre su traza: ¿se fue el tiempo en recuperar o en generar?

Listo cuando: el dashboard muestra datos de la corrida de evaluación y las capturas están en `docs/img/`.

### Paso 10 — Informe y demo

1. Completa `docs/evidencias.md`: checklist, tabla de `top_k`, evaluación con veredictos, experimentos y conclusiones apoyadas en lo medido.
2. Actualiza `README.md` y `docs/evidencias.md` para quitar las referencias a TecnoFábrica.
3. Haz la demo de 30 minutos con el Product Owner (plan-product-owner, paso 9).
4. Deja el stack como lo encontraste: `docker compose down` (sin `-v`).

## Riesgos que vigilas

| Riesgo | Señal | Qué hacer |
|---|---|---|
| Fichas partidas por el chunker | Más fragmentos que documentos, respuestas con datos a medias | Paso 3c |
| Español contra datos en inglés | hit@1 bajo en preguntas con alias | Alias y nombres bilingües en las fichas |
| El modelo no suma ni compara | Fallos en `kpi`, `ranking` y `comparacion` | Documentos pre-calculados y, si hace falta, el experimento F |
| Alucinación ante lo que falta | Respuestas con cifras en `abstencion` | Endurecer el prompt, bajar la temperatura |
| Primera consulta lenta | Latencias dispares | Distinguir frío de caliente en las mediciones |
| El modelo mezcla idiomas | Respuestas en inglés o chino | Reforzar «responde en español» en el prompt |

## Qué no te toca

Generar o editar los documentos del corpus ni los datos de origen: si algo no cuadra, devuélvelo al Data Engineer con el nombre del archivo y la pregunta que falló. Tampoco decides las metas de aceptación: las define el Product Owner.
