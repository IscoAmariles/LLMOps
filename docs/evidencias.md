# Evidencias del laboratorio

Informe a entregar al terminar el laboratorio. Las conclusiones deben sustentarse en resultados observados, no en suposiciones.

## Checklist

- [ ] 1. Arquitectura de los cinco servicios desplegados con Docker Compose (`docker compose ps`)
- [ ] 2. Captura de Ollama ejecutando el modelo local
- [ ] 3. Archivos documentales e indexación RAG (`POST /indexar`, `datos/indice.json`)
- [ ] 4. Una consulta y los fragmentos recuperados
- [ ] 5. Captura de una traza completa en MLflow (`pipeline_rag` → `recuperar_documentos` + `generar_respuesta_llm`)
- [ ] 6. Consultas PromQL para tokens, latencia y similitud
- [ ] 7. Dashboard de Grafana funcionando (`Monitoreo LLMOps: Ollama y RAG`)
- [ ] 8. Comparación de al menos tres valores de `top_k`
- [ ] 9. Análisis de temperatura, preguntas sin evidencia y calidad
- [ ] 10. Conclusiones

## Comparación de `top_k`

Pregunta usada: `¿Qué debe hacer un operario si encuentra una condición insegura?` (temperatura 0.2, solo cambia `top_k`).

| Indicador | K = 1 | K = 3 | K = 5 |
|---|---|---|---|
| Tiempo RAG (s) | | | |
| Tokens entrada | | | |
| Tokens salida | | | |
| Similitud máxima | | | |
| Fuentes relevantes | | | |
| Respuesta correcta | | | |

Análisis: ¿más contexto implica necesariamente mejor respuesta? ¿Qué configuración logra una respuesta correcta usando menos recursos?

## Evaluación con preguntas de referencia

Resultados de `python app/evaluacion.py` (`datos/resultados.json`). Clasifica cada respuesta contrastándola con las políticas originales.

| id | Pregunta | Esperada | Generada | Clasificación (correcta / incompleta / inventada) |
|---|---|---|---|---|
| 1 | ¿Cada cuánto se realiza mantenimiento preventivo? | Cada 30 días | | |
| 2 | ¿Cuál es el nivel mínimo de inventario? | 100 unidades por referencia | | |
| 3 | ¿Cuál es el inventario de seguridad? | 50 unidades por referencia | | |
| 4 | ¿Qué se hace ante una falla crítica? | Detener la máquina inmediatamente | | |
| 5 | ¿Quién autoriza la puesta en funcionamiento? | El supervisor de mantenimiento | | |
| 6 | ¿Qué hacer ante una condición insegura? | Detener la operación e informar al supervisor | | |
| 7 | ¿Quién verifica los movimientos de inventario? | El responsable de almacén | | |
| 8 | ¿Cuál es el salario del gerente? | No existe información suficiente | | |

## Experimentos

- **A. Tamaño del contexto:** observaciones sobre tokens de entrada, duración y relevancia con `top_k` = 1, 3 y 5.
- **B. Temperatura:** variabilidad observada con 0, 0.5 y 1 (varias repeticiones por pregunta).
- **C. Preguntas sin evidencia:** ¿el modelo reconoce la ausencia de datos o inventa información?
- **D. Rendimiento:** comportamiento de las métricas con 1, 5 y 10 consultas secuenciales; diferencia entre arranque en frío y modelo cargado (`load_duration`).

## Conclusiones

_Redactar aquí, apoyadas en los resultados anteriores._
