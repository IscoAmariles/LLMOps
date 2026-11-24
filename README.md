# Laboratorio LLMOps: RAG local con Ollama, MLflow, Prometheus y Grafana

Aplicación que responde preguntas sobre las políticas de **TecnoFábrica** (empresa ficticia) usando un LLM local, y que permite observar cada consulta: tokens consumidos, latencias, documentos recuperados y trazas por etapa.

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
│   ├── rag.py            # lectura, fragmentos, embeddings, similitud coseno, top_k
│   ├── metricas.py       # Counters e Histograms de Prometheus
│   └── evaluacion.py     # corre las preguntas de referencia contra la API
├── documentos/           # base documental (mantenimiento, inventarios, seguridad)
├── datos/                # índice vectorial y evaluación (indice.json y resultados.json se generan)
├── docs/                 # documentación de apoyo y plantilla de evidencias
├── mlflow/Dockerfile
├── prometheus/prometheus.yml
└── grafana/provisioning/datasources/datasource.yml
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
curl -X POST http://localhost:8000/indexar

curl -s -X POST http://localhost:8000/preguntar \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Cada cuánto se realiza el mantenimiento preventivo?", "top_k": 3, "temperatura": 0.2}'
```

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

**Dashboard (Grafana).** La fuente de datos Prometheus se provisiona sola. Crea el dashboard `Monitoreo LLMOps: Ollama y RAG` con estos paneles:

| Panel | Tipo | Expresión |
|---|---|---|
| Consultas procesadas | Stat | `sum(llm_consultas_total)` |
| Tokens entrada | Stat | `llm_tokens_entrada_total` |
| Tokens salida | Stat | `llm_tokens_salida_total` |
| Latencia media | Time series | `rate(llm_duracion_segundos_sum[5m]) / rate(llm_duracion_segundos_count[5m])` |
| Recuperación media | Time series | `rate(rag_recuperacion_segundos_sum[5m]) / rate(rag_recuperacion_segundos_count[5m])` |
| Similitud promedio | Time series | `rate(rag_similitud_sum[5m]) / rate(rag_similitud_count[5m])` |

## Evaluación con preguntas de referencia

`datos/preguntas_evaluacion.csv` tiene 8 preguntas con respuesta esperada; la última (salario del gerente) no tiene respaldo documental a propósito, para detectar respuestas inventadas.

```bash
sudo apt install python3-venv -y
python3 -m venv .venv
source .venv/bin/activate
pip install requests
python app/evaluacion.py
```

Genera `datos/resultados.json`. El script solo recopila evidencia: **no calcula exactitud semántica**. Hay que contrastar cada respuesta con las políticas y clasificarla como correcta, incompleta o inventada.

## Experimentos sugeridos

- **A. Tamaño del contexto:** `top_k` = 1, 3 y 5; compara tokens de entrada, duración y relevancia.
- **B. Temperatura:** 0, 0.5 y 1, repitiendo cada pregunta varias veces.
- **C. Preguntas sin evidencia:** salario del gerente, facturación, número de empleados.
- **D. Rendimiento:** 1, 5 y 10 consultas secuenciales, controlando si el modelo ya estaba cargado en memoria.

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
