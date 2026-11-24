# Plan de trabajo — Product Owner

> Escrito para: el Product Owner del laboratorio. Contexto, entregables compartidos y decisiones abiertas están en [plan-equipo.md](plan-equipo.md).

## Tu misión

Decidir **qué** debe hacer el asistente de datos verdes y **cómo sabremos que lo hace bien**. Tú no escribes código ni respuestas: defines alcance, decides, aportas las preguntas que importan y aceptas (o no) el resultado con evidencia.

Tu trabajo desbloquea a los otros dos roles: sin tus decisiones D1–D7 y el banco de preguntas, el Data Engineer no puede cerrar el corpus ni el LLM Engineer fijar el comportamiento ante lo que no sabe.

## Antes de empezar

- Lee [plan-equipo.md](plan-equipo.md), sobre todo las secciones 3 (dataset) y 7 (decisiones).
- Hojea el `README.md` del ETL (`C:\GitProjects\Laboratorio-MLOps-green-data-etl\README.md`), son 77 líneas.
- Ten a mano el [README del laboratorio](../README.md) para las URLs: API http://localhost:8000/docs, MLflow http://localhost:5000, Prometheus http://localhost:9090 y Grafana http://localhost:3000.

## Paso a paso

### Paso 1 — Entender el dato (30 min)

Qué: leer el contexto y quedarte con tres ideas, porque condicionan todo lo demás.

1. El dataset es **tabular y pequeño**: 20 países, una sola foto, sin año ni unidad.
2. Son **datos de laboratorio, no estadísticas oficiales**.
3. Un asistente sobre tablas es bueno buscando **un país** y flojo **sumando o comparando**; por eso el Data Engineer pre-calculará rankings y resúmenes como documentos.

Listo cuando: puedes explicar en una frase qué sabe y qué no sabe el asistente.

### Paso 2 — Escribir el enunciado y el alcance

Qué: completar esta plantilla y dejarla al inicio de tu rama, en `docs/alcance.md`.

```markdown
## Enunciado
Para <quién consulta> que necesita <qué necesita>,
el asistente de datos verdes es <qué es> que <beneficio>.
A diferencia de <alternativa>, <diferenciador>.

## Dentro del alcance
- Consultas sobre los 20 países del dataset y los 7 KPIs
- ...

## Fuera del alcance
- Evolución temporal, CO₂, tipos de energía, países fuera de los 20, unidades
- ...
```

Listo cuando: el alcance «fuera» coincide con la lista de lo que el dataset no contiene (plan-equipo §3).

### Paso 3 — Resolver las decisiones D1–D7 (sesión de 30 min con los otros dos roles)

Qué: recorrer la tabla de [plan-equipo.md §7](plan-equipo.md#7-decisiones-abiertas). Cada decisión trae una recomendación: confírmala o cámbiala.

Cómo: escribe tu decisión y la fecha en la última columna de esa tabla.

Prioridad: **D1, D2, D4 y D6** bloquean al Data Engineer; **D3 y D5** al LLM Engineer. D7 la cierras en el Paso 6.

Pregunta de fondo para D5: si el asistente no sabe, ¿preferimos que **calle** o que **intente ayudar**? La recomendación es callar con una frase fija: en datos de laboratorio, una respuesta inventada es peor que ninguna.

Listo cuando: ninguna fila queda vacía.

### Paso 4 — Escribir las historias de usuario

Qué: convertir el alcance en historias con criterios de aceptación comprobables. Punto de partida:

| ID | Historia | Criterio de aceptación (Dado / Cuando / Entonces) |
|---|---|---|
| HU-01 | Como analista, quiero consultar la ficha de un país por su nombre en español, en inglés o por código ISO | Dado un país de los 20, cuando pregunto por su participación renovable, entonces la respuesta da el valor correcto y cita su ficha |
| HU-02 | Como analista, quiero conocer los KPIs globales | Cuando pregunto cuántos países hay en cada estado, entonces responde con las cifras del dataset |
| HU-03 | Como analista, quiero rankings | Cuando pregunto qué país tiene mayor participación renovable, entonces nombra al correcto y su valor |
| HU-04 | Como analista, quiero comparar regiones o niveles de ingreso | Cuando pregunto por una región, entonces lista sus países y el promedio, indicando que es promedio simple |
| HU-05 | Como estudiante, quiero entender la clasificación | Cuando pregunto qué significa `Critical`, entonces explica el umbral y aclara que es una regla del laboratorio |
| HU-06 | Como responsable del producto, quiero que no invente | Cuando pregunto por algo fuera del dataset, entonces responde con la frase de abstención (D5) |
| HU-07 | Como equipo, queremos trazabilidad | Cada consulta deja traza en MLflow, queda reflejada en Prometheus y las fuentes recuperadas se ven en la respuesta |

Listo cuando: cada historia tiene al menos dos preguntas del banco (Paso 5) que la prueban.

### Paso 5 — Crear el banco de preguntas

Qué: crear `datos/banco_preguntas.csv`, UTF-8, columnas `id,tipo,pregunta,historia,prioridad`, con **mínimo 30 preguntas**.

| Tipo | Cantidad mínima | Qué pone a prueba |
|---|---|---|
| `pais` | 10 | Buscar un dato de un país, con variantes de nombre |
| `kpi` | 4 | Cifras globales |
| `ranking` | 4 | Máximos, mínimos, posiciones |
| `comparacion` | 4 | Regiones y niveles de ingreso |
| `explicacion` | 2 | Reglas, fórmulas y glosario |
| `abstencion` | 6 | Lo que **no** puede responder |

Ejemplos de formato (prioridad 1 = imprescindible):

```csv
id,tipo,pregunta,historia,prioridad
1,pais,¿Qué participación renovable tiene Noruega?,HU-01,1
2,pais,¿Cuál es la capital de Egipto?,HU-01,2
3,pais,What is the environmental status of Colombia?,HU-01,2
4,kpi,¿Cuántos países están en estado Green?,HU-02,1
5,ranking,¿Qué país consume más energía?,HU-03,1
6,comparacion,¿Qué países de América Latina están en estado Critical?,HU-04,1
7,explicacion,¿Qué significa que un país esté en estado Moderate?,HU-05,2
8,abstencion,¿Cuántas toneladas de CO2 emite Alemania?,HU-06,1
```

Buenas prácticas:

- Mezcla español, inglés, alias («EE. UU.») y alguna pregunta mal escrita: así se prueba la recuperación.
- Para `abstencion` cubre cada cosa que el dataset no tiene: un país fuera de los 20 (Italia), CO₂, evolución en el tiempo (2015–2020), desglose por tipo de energía, unidad de medida (la respuesta correcta es «no está documentada») y un dato inexistente (población).
- **No escribas las respuestas.** El Data Engineer las deriva del dato para que no haya errores de transcripción.

Listo cuando: el archivo tiene el mínimo por tipo y cada fila apunta a una historia.

### Paso 6 — Definir la rúbrica y las metas de aceptación (D7)

Rúbrica de clasificación de cada respuesta:

| Veredicto | Significa |
|---|---|
| Correcta | Contiene el valor esperado y no se contradice |
| Incompleta | Es parcialmente correcta o omite una parte pedida |
| Inventada | Afirma datos que no están en los documentos |

Metas **provisionales** (ajústalas tras la primera medición):

| Indicador | Meta |
|---|---|
| Correctas en `pais` | ≥ 90 % |
| Correctas en `kpi`, `ranking` y `comparacion` | ≥ 70 % (un modelo de 1.5 B parámetros suele fallar al agregar) |
| Correctas en `explicacion` | ≥ 80 % |
| Abstención correcta en `abstencion` | ≥ 90 % (como máximo 1 inventada de 6) |
| La fuente esperada aparece entre las 3 recuperadas, en `pais` | ≥ 95 % |
| Consultas con `estado="error"` | 0 |
| Latencia p95 | Se fija después de la primera medición |

Listo cuando: las metas están anotadas en D7 de plan-equipo §7.

### Paso 7 — Aceptar cada traspaso

No avances de fase hasta revisar cada entrega con su checklist.

**Entrega del Data Engineer** (fin de la fase 2):

- [ ] `datos/fuente/PROCEDENCIA.md` indica rama `feat/airflow-medallion-alignment` y commit.
- [ ] `docs/contrato-datos.md` muestra los controles de calidad y su resultado.
- [ ] `documentos/` tiene 27 archivos `.txt` y el ejemplo de TecnoFábrica está aparte.
- [ ] `datos/preguntas_evaluacion_green.csv` tiene una fila por cada pregunta del banco.
- [ ] Las fichas avisan que son datos de laboratorio sin unidad ni año (D3).

**Entrega del LLM Engineer** (fin de la fase 3):

- [ ] Resultados de la evaluación contra las metas del Paso 6.
- [ ] Tabla de experimentos (`top_k`, temperatura, abstención, rendimiento) en `docs/evidencias.md`.
- [ ] Dashboard de Grafana y trazas de MLflow listos para la demo.

### Paso 8 — Prueba de aceptación (UAT)

Qué: probar tú mismo el asistente con 12 preguntas del banco (al menos 2 de cada tipo), sin saber de antemano cómo responde.

Cómo:

1. Abre http://localhost:8000/docs → `POST /preguntar` → **Try it out**.
2. Pega el cuerpo y pulsa **Execute**:
   ```json
   { "pregunta": "¿Qué participación renovable tiene Noruega?", "top_k": 3, "temperatura": 0.2 }
   ```
3. Lee `respuesta`, y en `fuentes` el archivo (`fuente`) y la `similitud`. Revisa también `tokens_entrada`, `tokens_salida` y los tiempos.
4. Compara con el dato (`datos/fuente/gold_final.csv`) y anota el veredicto de la rúbrica.

Recuerda: **una similitud alta no prueba que la respuesta sea correcta.** Mira siempre qué fuente trajo y si la respuesta se apoya en ella.

Registra en una tabla: `id | pregunta | ¿fuente correcta? | veredicto | comentario`.

Listo cuando: las 12 filas están completas y comparas tu veredicto con el del LLM Engineer; si difieren, esa diferencia es un hallazgo.

### Paso 9 — Demo de observabilidad (30 min con el LLM Engineer)

Pídele que te muestre, con una consulta en vivo:

1. **La traza en MLflow** (`pipeline_rag` → `recuperar_documentos` + `generar_respuesta_llm`): ¿qué documentos trajo y cuánto tardó cada etapa?
2. **El dashboard de Grafana**: consultas, tokens de entrada y salida, latencia media y similitud promedio.
3. **La consulta más lenta**: ¿el tiempo se fue en recuperar o en generar?

Pregunta clave: con lo que vemos, ¿podríamos detectar un problema en producción? ¿Falta alguna métrica?

### Paso 10 — Cierre

1. Completa la parte de aceptación de `docs/evidencias.md` con tu veredicto *go / no-go* y las razones.
2. Confirma por escrito el aviso «datos de laboratorio, no estadísticas oficiales».
3. Verifica los términos de uso de los datos del World Bank y del CSV de energía antes de compartir el sistema fuera del equipo. El repo ETL no tiene LICENSE.
4. Prioriza el backlog siguiente, por ejemplo:
   - leer los datos del warehouse Postgres del ETL en lugar de los CSV;
   - regenerar el corpus automáticamente cuando el ETL se ejecute;
   - documentar la unidad, el año y la fuente del CSV de energía con quien lo creó;
   - ampliar a más países o incorporar series de tiempo.

## Riesgos que vigilas

| Riesgo | Cómo se ve | Qué hacer |
|---|---|---|
| El modelo suma o compara mal | Fallan `kpi`, `ranking` y `comparacion` | Documentos pre-calculados (ya previstos) y metas realistas |
| Preguntas en español sobre datos en inglés | La ficha correcta no aparece en `fuentes` | Alias y nombres bilingües en el corpus (D2) |
| Datos con la regla vieja | Cifras que no coinciden con este plan | Verificar la rama del ETL (D4) |
| Respuestas que parecen oficiales | Cifras sin aviso | Mantener D3 en fichas y prompt |

## Qué no te toca

Escribir código, generar documentos o ejecutar comandos de Docker. Si necesitas ver algo corriendo, pídeselo al LLM Engineer.
