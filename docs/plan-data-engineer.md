# Plan de trabajo — Data Engineer

> Escrito para: el Data Engineer del laboratorio. Contexto, entregables compartidos y decisiones abiertas están en [plan-equipo.md](plan-equipo.md).

¡Hola! Gracias por encargarte de la parte que sostiene todo lo demás. El modelo solo puede ser tan confiable como los datos que le entregues, y eso lo decide tu cuidado: qué datos congelas, cómo los validas y cómo los conviertes en texto. Si en algún paso algo no cuadra, **es buena señal**: significa que el control funcionó. Avisa al equipo con la evidencia y lo resolvemos juntos.

## Tu misión

Convertir la capa Gold del ETL en dos cosas que el resto del equipo pueda usar con confianza:

1. Un **snapshot validado** de los datos, con procedencia clara.
2. Un **corpus de 27 documentos de texto** y un **conjunto de evaluación** derivado de esos mismos datos.

## Antes de empezar

- Lee [plan-equipo.md](plan-equipo.md): el dataset (§3), los entregables (§5) y las decisiones (§7). Tus decisiones son **D1, D2, D4 y D6**; si el Product Owner aún no las cerró, aplica las recomendaciones.
- Necesitas Python 3 y Git. Los scripts usan solo la biblioteca estándar (no necesitas pandas). Para las pruebas del paso 9 necesitarás `pytest`.
- **No necesitas Docker ni Airflow del ETL**: los CSV Gold ya están en el repo. Así ahorras memoria para Ollama.

## Paso a paso

### Paso 1 — Verificar la rama del ETL

```powershell
$ETL = "C:\GitProjects\Laboratorio-MLOps-green-data-etl"
git -C $ETL branch --show-current      # debe decir: feat/airflow-medallion-alignment
git -C $ETL status --short             # vacío = sin cambios locales
git -C $ETL rev-parse --short HEAD     # anótalo: es la procedencia
```

**Cuidado:** la rama `main` de ese repo es una versión antigua (5 países, columna `Emission_Efficiency`, otra regla de clasificación). Si estás en `main`, no sigas: avisa al equipo. Cambiar de rama modifica la carpeta de trabajo del ETL, así que, si lo haces, deja el repo como lo encontraste al terminar.

Listo cuando: estás en la rama correcta y tienes anotado el commit.

### Paso 2 — Mirar los datos con calma

```powershell
Get-Content "$ETL\data\gold\gold_final.csv" -TotalCount 1       # cabecera: 12 columnas
(Import-Csv "$ETL\data\gold\gold_final.csv").Count               # 20
Import-Csv "$ETL\reports\kpis.csv" | Format-Table                # 7 KPIs
```

No hace falta regenerar el pipeline. Si decides ejecutar `python main.py` en el ETL, sobrescribirá CSV que están versionados allí y la lista de países de `countries_raw.csv` puede variar: revisa `git status` en ese repo y **no hagas commit allí**.

Listo cuando: ves 12 columnas, 20 filas y 7 KPIs.

### Paso 3 — Congelar el snapshot en este repo

```powershell
New-Item -ItemType Directory -Force datos\fuente | Out-Null
Copy-Item "$ETL\data\gold\gold_final.csv" datos\fuente\
Copy-Item "$ETL\reports\kpis.csv" datos\fuente\
```

Crea `datos/fuente/PROCEDENCIA.md` con: repo de origen, rama, **commit completo** (`git -C $ETL rev-parse HEAD`), fecha de copia, archivos copiados y quién los copió. Con eso cualquiera puede reproducir exactamente lo que se indexó.

Listo cuando: los dos CSV y `PROCEDENCIA.md` están en `datos/fuente/`.

### Paso 4 — Contrato de datos y controles de calidad

El ETL valida que existan archivos, columnas y filas, pero **no valida rangos ni coherencias**. Ese cuidado extra es tuyo.

Escribe `scripts/validar_gold.py` (biblioteca estándar) que lea `datos/fuente/` e imprima `PASS` o `FAIL` por control, y devuelva código de salida distinto de cero si algo falla:

| # | Control |
|---|---|
| C1 | Las 12 columnas existen, con esos nombres y en ese orden |
| C2 | Número de filas (hoy 20); si cambia, avisa, porque el corpus se genera por fila |
| C3 | `Country_Code` único y de 3 letras mayúsculas |
| C4 | Ninguna celda vacía |
| C5 | `Energy_Consumption` > 0 y `Renewable_Energy` ≥ 0, ambos numéricos |
| C6 | `Renewable_Energy` ≤ `Energy_Consumption` |
| C7 | `Renewable_Share` entre 0 y 1 y coherente con `Renewable_Energy / Energy_Consumption` |
| C8 | `Energy_per_Renewable_Unit` coherente con `Energy_Consumption / (Renewable_Energy + 1)` |
| C9 | `Environmental_Status` coincide con los umbrales (`≥ 0.30` Green, `≥ 0.10` Moderate, `< 0.10` Critical), cuidando las fronteras exactas (China está justo en 0.10) |
| C10 | Los KPIs coinciden con el Gold: total de filas, promedios, máximo, mínimo y conteos de Green y Critical |

Documenta el esquema y los controles en `docs/contrato-datos.md`: tabla de columnas (nombre, tipo, nulos permitidos, rango, significado; parte está en plan-equipo §3), la lista de controles y el resultado de la última ejecución.

Si un control falla, **no lo arregles en silencio**: abre un reporte con la evidencia para quien mantiene el ETL y deja constancia en `docs/contrato-datos.md`.

Listo cuando: los 10 controles dan `PASS` (o los `FAIL` están reportados) y el contrato está documentado.

### Paso 5 — Tabla de alias de países

Los usuarios dirán «Egipto» o «EE. UU.»; el dato dice `Egypt, Arab Rep.` y `United States`. Crea `datos/alias_paises.csv` con columnas `Country_Code,nombre_es,nombre_en,alias` (alias separados por `|`; pon comillas en los nombres con coma):

| Country_Code | nombre_es | nombre_en (`Country` del Gold) | alias |
|---|---|---|---|
| ARG | Argentina | Argentina | |
| AUS | Australia | Australia | |
| BRA | Brasil | Brazil | |
| CAN | Canadá | Canada | |
| CHL | Chile | Chile | |
| CHN | China | China | |
| COL | Colombia | Colombia | |
| EGY | Egipto | Egypt, Arab Rep. | Egypt |
| FRA | Francia | France | |
| DEU | Alemania | Germany | |
| IND | India | India | |
| JPN | Japón | Japan | |
| KEN | Kenia | Kenya | |
| MEX | México | Mexico | |
| NOR | Noruega | Norway | |
| PER | Perú | Peru | |
| ZAF | Sudáfrica | South Africa | |
| ESP | España | Spain | |
| USA | Estados Unidos | United States | EE. UU.\|EEUU\|USA |
| URY | Uruguay | Uruguay | |

Agrega los alias que se te ocurran (con y sin tilde). Valida que los 20 `Country_Code` coincidan con los del Gold.

Listo cuando: hay 20 filas y el script del paso 6 las cruza con el Gold sin sobrantes ni faltantes.

### Paso 6 — Generar el corpus de documentos

El asistente lee los `.txt` de `documentos/` (solo ese nivel, no subcarpetas) y los parte en fragmentos de **500 caracteres** con 80 de solapamiento. Para que cada recuperación traiga información completa, diseña los textos así:

- Cada **ficha de país cabe en un solo fragmento** (≤ 500 caracteres, saltos de línea incluidos).
- Los documentos largos se organizan en **bloques separados por una línea en blanco**; cada bloque es autosuficiente (≤ 500 caracteres) y **empieza con su propio título**, para que se entienda aunque llegue solo.
- Formato numérico único: **punto decimal** y porcentajes con **un decimal** (`90.9 %`), mismo formato en todo el corpus y en las respuestas esperadas.
- Todo se calcula desde `datos/fuente/`; nada se escribe a mano ni se copia desde este plan.

Escribe `scripts/generar_documentos.py` (biblioteca estándar, UTF-8, saltos de línea LF) con estas reglas:

- **Idempotente:** ejecutarlo dos veces seguidas no cambia ningún archivo (`git status` queda limpio la segunda vez).
- **Con aserciones:** falla si una ficha supera 500 caracteres o si faltan países en la tabla de alias.
- Orden determinista (por `Country_Code`) y, en los empates (Argentina y Brasil tienen ambos 9.0 %), desempate por `Country_Code`, **dicho en el texto** («empate»).

Archivos a generar en `documentos/` (**27** en total):

| Archivo | Cant. | Contenido |
|---|---|---|
| `pais_<ISO3>.txt` | 20 | Ficha por país (plantilla abajo) |
| `kpis.txt` | 1 | Bloque con los 7 KPIs; bloque con el país de mayor y menor consumo (el KPI solo da el número); bloques de países por estado (Green, Moderate, Critical) con su participación |
| `ranking_participacion_renovable.txt` | 1 | Los 20 países de mayor a menor participación, en bloques de 5 (puestos 1–5, 6–10…), cada uno con su título |
| `resumen_por_region.txt` | 1 | Un bloque por región: cuántos países, cuáles, participación promedio **simple** y conteo por estado |
| `resumen_por_nivel_ingreso.txt` | 1 | Un bloque por nivel de ingreso, con lo mismo |
| `metodologia.txt` | 1 | Fórmulas de `Renewable_Share`, `Energy_per_Renewable_Unit` (explica el `+1` y que **no mide emisiones**), umbrales de estado y aclaración de que son reglas del laboratorio |
| `glosario.txt` | 1 | Una entrada por columna del Gold, en bloques cortos |
| `limitaciones.txt` | 1 | Lo que el dataset no tiene (año, unidad, CO₂, tipos de energía, más países) y que son datos de laboratorio, no estadísticas oficiales |

**Plantilla de ficha** (ejemplo con Noruega; los valores salen del Gold):

```text
Ficha de país: Noruega (Norway), código NOR. También conocido como: Noruega, Norway, NOR.
Capital: Oslo. Región: Europe & Central Asia (Europa y Asia Central). Nivel de ingreso: High income (ingreso alto).
Consumo de energía: 220. Energía renovable: 200. Participación renovable: 90.9 % (Renewable_Share = 0.909).
Estado ambiental: Green (verde: participación renovable ≥ 30 %).
Nota: datos de laboratorio, no estadísticas oficiales; sin unidad ni año documentados.
```

Con nombres de región largos (p. ej. Egipto) es probable que la ficha se pase de 500 caracteres. Recorta primero la traducción de la región o la línea de alias, **nunca los números**.

Las etiquetas `Green`, `Moderate` y `Critical` se explican en español (verde, moderado, crítico) para que preguntas como «¿qué países están en estado crítico?» encuentren sus documentos.

Listo cuando: `documentos/` tiene exactamente 27 `.txt` de datos verdes, el script es idempotente y todas las aserciones pasan.

### Paso 7 — Apartar el corpus de ejemplo (según D1)

Con D1 confirmado, mueve las políticas de TecnoFábrica fuera del nivel que se indexa. Si ya existe el commit inicial, usa `git mv`; si no, `Move-Item`:

```powershell
New-Item -ItemType Directory -Force documentos\ejemplo_tecnofabrica | Out-Null
git mv documentos\mantenimiento.txt documentos\inventarios.txt documentos\seguridad.txt documentos\ejemplo_tecnofabrica\
```

(La subcarpeta no se indexa porque la lectura de `documentos/` no es recursiva.) El CSV de evaluación de ejemplo lo mueve el LLM Engineer: coordínense para no tocar los mismos archivos.

Listo cuando: en `documentos/` solo quedan los 27 archivos nuevos.

### Paso 8 — Conjunto de evaluación con respuestas derivadas del dato

Con el banco de preguntas del Product Owner (`datos/banco_preguntas.csv`), crea `datos/preguntas_evaluacion_green.csv` con el [contrato de plan-equipo §5](plan-equipo.md#contrato-del-conjunto-de-evaluación): `id,tipo,pregunta,respuesta_esperada,terminos_clave,fuente_esperada`.

- Una fila por pregunta del banco, con el mismo `id`, `tipo` y `pregunta`.
- Para cada pregunta contestable, toma el valor del **dato o de los documentos que generaste**, no de tu memoria. `terminos_clave` son las cadenas que deben aparecer en una buena respuesta (por ejemplo `90.9|Noruega`). `fuente_esperada` es el archivo donde está la respuesta (p. ej. `pais_NOR.txt`).
- Para `abstencion`: `respuesta_esperada` con la frase fija de la decisión D5, `terminos_clave` con sus palabras esenciales y `fuente_esperada` vacío.

Escribe `scripts/validar_evaluacion.py` para que el archivo **no se desvíe** de los documentos. Debe comprobar que:

- los `id` son únicos y los `tipo` válidos;
- cada `fuente_esperada` existe en `documentos/`;
- cada término de `terminos_clave` aparece en el texto de su `fuente_esperada` (en las filas que no son de abstención).

Listo cuando: el validador pasa y no hay ninguna pregunta del banco sin fila.

### Paso 9 — Pruebas (estilo del ETL)

El ETL usa pytest con `tmp_path` y CSV mínimos construidos dentro de cada prueba. Haz lo mismo en `tests/test_generar_documentos.py`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install pytest
python -m pytest
```

Cubre, como mínimo: una ficha por país y ninguna pasa de 500 caracteres; el empate de Argentina y Brasil; la frontera exacta de 0.10; la idempotencia; el formato decimal.

Listo cuando: `python -m pytest` está en verde.

### Paso 10 — Entregar al LLM Engineer

1. Haz commit en tu rama (`feat/de-corpus-green`) con mensajes tipo `feat(corpus): generate green data documents`.
2. Avisa con un mensaje corto que incluya:
   - rama y commit del ETL usados (`PROCEDENCIA.md`);
   - resultado de los controles (`PASS`/`FAIL`);
   - cantidad de documentos (**27**) y la cantidad esperada que devuelva `POST /indexar` (`"documentos": 27`);
   - cualquier hallazgo sobre el dato.
3. Quédate disponible: si la recuperación falla para algún país, lo más probable es que haya que mejorar los alias o el texto de la ficha.

Listo cuando: el LLM Engineer indexó tu corpus y no encontró fichas partidas ni datos inconsistentes.

## Cuando el ETL vuelva a ejecutarse

El DAG del ETL está programado `@daily`, pero solo corre si su stack está encendido. Cuando haya datos nuevos:

```powershell
# 1. repite el Paso 1 (rama y commit) y el Paso 3 (copiar el snapshot y actualizar PROCEDENCIA.md)
python scripts\validar_gold.py
python scripts\generar_documentos.py
python scripts\validar_evaluacion.py
Invoke-RestMethod -Method Post http://localhost:8000/indexar     # reindexar (lo hace el LLM Engineer)
```

Si el número de países cambia, avisa: las preguntas de evaluación y las metas del Product Owner dependen de él.

Para una versión futura: leer directamente del warehouse Postgres del ETL (`localhost:5433`, base `green_dw`, tablas `gold_green_data` y `kpis`, credenciales de laboratorio) en lugar de los CSV.

## Qué no te toca

- Modificar el repo del ETL o hacer commits allí.
- Escribir cifras a mano en documentos o respuestas esperadas.
- Tocar el prompt, el chunker o la API: eso es del LLM Engineer.

¡Gracias! Con este cuidado, el resto del equipo puede confiar en lo que mide.
