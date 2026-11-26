# Laboratorio LLMOps: RAG local con Ollama, MLflow, Prometheus y Grafana

Asistente que responde **en español** preguntas sobre el dataset **Green Data** (20 países: consumo de energía, participación renovable y estado ambiental) usando un LLM local, y que permite observar cada consulta: tokens consumidos, latencias, documentos recuperados y trazas por etapa. Los datos son de laboratorio, sin unidad ni año documentados; cuando el contexto no respalda la respuesta, el asistente dice «No existe información suficiente en los documentos.».

La organización del trabajo por roles está en [docs/README.md](docs/README.md).

Implementa la guía *LLMOps desde cero en Windows con WSL2 y Docker* de Juan Manuel Núñez Velasco.

## Arquitectura

```
Usuario · Pregunta
        │
   API Python · FastAPI
   ┌────┴─────┐
RAG · Recuperación ──► Ollama · LLM local
   └────┬─────┘
 Observabilidad y seguimiento
  MLflow (trazas) · Prometheus (métricas) ──► Grafana (dashboard)
```

| Servicio   | Función                                     | URL local                  |
|------------|---------------------------------------------|----------------------------|
| Ollama     | LLM (`qwen2.5:1.5b`) y embeddings (`nomic-embed-text`) | http://localhost:11434 |
| API        | FastAPI: `/indexar`, `/preguntar`, `/metrics`, `/health` | http://localhost:8000/docs |
| MLflow     | Trazas de recuperación y generación         | http://localhost:5000      |
| Prometheus | Recolección de métricas cada 5 s            | http://localhost:9090      |
| Grafana    | Dashboards (usuario/clave de laboratorio: `admin` / `admin`) | http://localhost:3000 |

Todos los puertos se publican solo en `127.0.0.1`.

## Estructura

```
.
├── docker-compose.yml
├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py           # API FastAPI + trazas MLflow + /metrics
│   ├── rag.py            # lectura, embeddings, similitud coseno, top_k
│   ├── fragmentacion.py  # chunkers: caracteres (original) y parrafos
│   ├── metricas.py       # Counters e Histograms de Prometheus
│   └── evaluacion.py     # evaluación parametrizada: chequeos, hit@k, MLflow
├── documentos/           # 27 documentos de datos verdes (20 fichas + 7 de apoyo); ejemplo_tecnofabrica/ no se indexa
├── datos/                # snapshot Gold, alias, conjunto de evaluación; indice*.json y resultados_*.json se generan
├── scripts/, tests/      # generador y validadores del corpus; pruebas (pytest)
├── docs/                 # planes por rol, bitácora y evidencias
├── mlflow/Dockerfile
├── prometheus/prometheus.yml
└── grafana/provisioning/ # datasource y dashboard provisionados
```

## Requisitos

- Docker Desktop (con integración WSL2 si trabajas desde Ubuntu).
- ~16 GB de RAM recomendados; con menos funciona más lento.
- Internet para la primera descarga de imágenes y modelos.

> La guía recomienda trabajar dentro del sistema de archivos Linux de WSL (`~/proyectos`) y no desde `/mnt/c/`. Si clonas este repo en Windows, `docker compose` funciona igual desde PowerShell con Docker Desktop, pero los bind mounts son más lentos.

## Puesta en marcha

Desde la raíz del repo:

```bash
docker compose config          # valida el compose
docker compose build
docker compose up -d
docker compose ps              # deben aparecer los 5 servicios
```

Descarga los modelos (se guardan en el volumen `ollama_data`):

```bash
docker compose exec ollama ollama pull qwen2.5:1.5b
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama list
```

Indexa los documentos y haz una consulta:

```bash
curl -X POST http://localhost:8000/indexar                      # documentos: 27
curl -X POST "http://localhost:8000/indexar?chunker=parrafos"   # alternativa: corta en líneas en blanco

curl -s -X POST http://localhost:8000/preguntar \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Qué participación renovable tiene Noruega?", "top_k": 3, "temperatura": 0.2}'
```

El chunker por defecto se cambia con la variable de entorno `CHUNKER` del servicio `api` (`caracteres` o `parrafos`). Cada indexación escribe `datos/indice_meta.json` con el chunker y los fragmentos por archivo.

En PowerShell usa `curl.exe` (en lugar de `curl`) o la interfaz Swagger en http://localhost:8000/docs.

La respuesta incluye la respuesta del modelo, `tokens_entrada`, `tokens_salida`, `duracion_ollama`, `duracion_generacion`, `tiempo_recuperacion` y las `fuentes` con su similitud.

## Observabilidad

**Trazas (MLflow).** Abre http://localhost:5000 → experimento `Laboratorio_RAG_Ollama` → *Traces*. Cada consulta genera:

```
pipeline_rag
├── recuperar_documentos
└── generar_respuesta_llm
```

**Métricas (Prometheus).** `curl -s http://localhost:8000/metrics | grep -E "llm_|rag_"`. Verifica que el target `llmops_api` esté `UP` en http://localhost:9090/targets.

| Métrica | Tipo | Significado |
|---|---|---|
| `llm_consultas_total{estado}` | Counter | Consultas por estado (`exito` / `error`) |
| `llm_tokens_entrada_total` | Counter | Tokens de entrada del LLM (no cuenta embeddings) |
| `llm_tokens_salida_total` | Counter | Tokens generados por el LLM |
| `llm_duracion_segundos` | Histogram | Duración total de `/preguntar` |
| `rag_recuperacion_segundos` | Histogram | Tiempo de recuperación documental |
| `rag_similitud` | Histogram | Similitud de los fragmentos recuperados |

Consultas PromQL útiles:

```promql
llm_consultas_total{estado="exito"}
rate(llm_tokens_salida_total[5m])
rate(llm_duracion_segundos_sum[5m]) / rate(llm_duracion_segundos_count[5m])
histogram_quantile(0.95, rate(llm_duracion_segundos_bucket[5m]))
rate(rag_similitud_sum[5m]) / rate(rag_similitud_count[5m])
```

**Dashboard (Grafana).** La fuente de datos Prometheus y el dashboard `Monitoreo LLMOps: Ollama y RAG` (carpeta *LLMOps*) se provisionan solos desde `grafana/provisioning/`. Paneles:

| Panel | Tipo | Expresión |
|---|---|---|
| Consultas procesadas | Stat | `sum(llm_consultas_total)` |
| Tokens entrada | Stat | `llm_tokens_entrada_total` |
| Tokens salida | Stat | `llm_tokens_salida_total` |
| Latencia media | Time series | `rate(llm_duracion_segundos_sum[5m]) / rate(llm_duracion_segundos_count[5m])` |
| Recuperación media | Time series | `rate(rag_recuperacion_segundos_sum[5m]) / rate(rag_recuperacion_segundos_count[5m])` |
| Similitud promedio | Time series | `rate(rag_similitud_sum[5m]) / rate(rag_similitud_count[5m])` |
| Latencia p95 | Time series | `histogram_quantile(0.95, rate(llm_duracion_segundos_bucket[5m]))` |
| Consultas con error | Stat | `sum(llm_consultas_total{estado="error"}) or vector(0)` |

## Evaluación con preguntas de referencia

`datos/preguntas_evaluacion_green.csv` tiene 30 preguntas (`pais`, `kpi`, `ranking`, `comparacion`, `explicacion` y `abstencion`) con respuesta esperada, `terminos_clave` y `fuente_esperada`. Las 6 de `abstencion` no tienen respaldo documental a propósito.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install requests "mlflow>=3.0,<4" pytest
python app\evaluacion.py --help
python app\evaluacion.py datos\preguntas_evaluacion_green.csv --top-k 3 --temperatura 0.2 --mlflow --etiqueta linea_base
```

Genera `datos/resultados_<fecha>.json` e imprime un resumen por tipo. Chequeos automáticos de primera pasada: `acierto_terminos` (todos los términos clave en la respuesta) y `hit_fuente` / `rango_fuente` (posición de la fuente esperada, para hit@1 y hit@3). **La clasificación final (correcta, incompleta, inventada) es manual.** Con `--mlflow` la corrida queda como run del experimento `Evaluacion_RAG_Green`, separado de las trazas del servicio. Otros parámetros: `--repeticiones`, `--ids`, `--tipos`, `--salida`.

Pruebas: `python -m pytest`.

## Experimentos

Resultados y conclusiones en [docs/evidencias.md](docs/evidencias.md).

- **A. Tamaño del contexto:** `top_k` = 1, 3 y 5; tokens de entrada, duración, acierto y hit@k por tipo.
- **B. Temperatura:** 0, 0.5 y 1, repitiendo cada pregunta 3 veces (`--repeticiones 3`).
- **C. Preguntas sin evidencia:** las 6 de `abstencion` (país fuera del dataset, CO₂, años, población…).
- **D. Rendimiento:** 1, 5 y 10 consultas secuenciales, en frío y en caliente.
- **E. Fragmentación:** `chunker=caracteres` frente a `chunker=parrafos`.

## Solución de problemas

| Problema | Comprobación |
|---|---|
| `docker` no existe dentro de Ubuntu | Docker Desktop → Settings → Resources → WSL Integration |
| Un contenedor se detiene | `docker compose ps -a` |
| Error en FastAPI | `docker compose logs --tail=100 api` |
| MLflow no responde | `docker compose logs --tail=100 mlflow` |
| Ollama no encuentra el modelo | `docker compose exec ollama ollama list` |
| Prometheus aparece `DOWN` | http://localhost:9090/targets y `/metrics` |
| Grafana no muestra datos | Revisa el datasource y la ventana temporal |
| Cambiaron dependencias de la API | `docker compose up -d --build api` |

Detener sin borrar datos: `docker compose down`. Reiniciar: `docker compose up -d`.
**No uses `docker compose down -v`** salvo que quieras borrar los volúmenes (modelos descargados y datos de observabilidad).

## Notas

- Las credenciales `admin/admin` de Grafana son solo para esta práctica local; cámbialas antes de compartir el sistema.
- Las imágenes usan `latest` por simplicidad. En un proyecto mantenido conviene fijar versiones concretas.
- `depends_on` solo controla el orden de arranque, no que el servicio esté listo; por eso la API espera a MLflow al iniciar.
- MLflow guarda preguntas, respuestas y contenido de documentos en las trazas. Usa solo datos ficticios o autorizados; en producción hacen falta controles de privacidad, acceso y retención.
- El índice vectorial es un JSON, suficiente para este ejercicio. Para volúmenes grandes considera Qdrant, Chroma, Milvus o pgvector.
- La similitud vectorial alta no garantiza que la respuesta sea correcta: la calidad requiere evaluación aparte.
