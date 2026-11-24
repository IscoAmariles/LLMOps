# Bitácora 01 · Reporte de ejecución · Data Engineer · Corpus de datos verdes

**Proyecto:** Laboratorio LLMOps, RAG de datos verdes  
**Fecha:** 2026-11-24  
**Elaborado por:** MJGG  
**Rol:** Data Engineer  
**Rama:** `feat/de-corpus-green` · **PR:** [#2](https://github.com/IscoAmariles/LLMOps/pull/2) (abierto, pendiente de revisión)  
**Plan ejecutado:** [plan-data-engineer.md](../plan-data-engineer.md), pasos 1 a 7 y 9  
**Commits:** `13aebad` (scripts y pruebas) y `6df20be` (snapshot y corpus)

## 1. Objetivo

Convertir la capa Gold del ETL Green Data en un snapshot validado con procedencia clara y en un corpus de documentos de texto listo para indexar en el RAG, para que el LLM Engineer pueda medir recuperación y respuestas.

## 2. Método

- Los scripts usan solo la biblioteca estándar de Python y leen únicamente `datos/fuente/`: ninguna cifra de los documentos se escribe a mano.
- Cada regla del plan quedó protegida por una prueba automatizada (pytest con CSV mínimos construidos en `tmp_path`, el mismo estilo del ETL).
- Antes de entregar se verificó en un clon limpio de la rama: pruebas, controles y una segunda generación de documentos sin cambios.
- Trabajo preparado con asistencia de Claude Code; los commits, el push y el PR los hizo MJGG.

## 3. Resultado por paso del plan

| Paso | Criterio de "listo" del plan | Evidencia | Estado |
|---|---|---|---|
| 1. Verificar la rama del ETL | Rama correcta y commit anotado | `datos/fuente/PROCEDENCIA.md`: commit `aa4c813` de `main`, que tiene el mismo árbol que `feat/airflow-medallion-alignment` (`684fba9`) | Hecho |
| 2. Mirar los datos | 12 columnas, 20 filas, 7 KPIs | Confirmado al validar (C1, C2 y C10) | Hecho |
| 3. Congelar el snapshot | Dos CSV y `PROCEDENCIA.md` en `datos/fuente/` | `gold_final.csv`, `kpis.csv` (LF, con blob git y SHA-256) y `PROCEDENCIA.md` | Hecho |
| 4. Contrato de datos y controles | 10 controles en PASS y contrato documentado | `scripts/validar_gold.py`: **10 de 10 en PASS**. `docs/contrato-datos.md` con esquema, controles, tolerancias y última ejecución | Hecho |
| 5. Alias de países | 20 filas que cruzan con el Gold | `datos/alias_paises.csv` con nombre en español, en inglés y alias (p. ej. «EE. UU.», «Egypt») | Hecho |
| 6. Generar el corpus | 27 `.txt`, script idempotente, aserciones en verde | `scripts/generar_documentos.py`: 20 fichas `pais_<ISO3>.txt` y 7 documentos de apoyo. Todas las fichas ≤ 500 caracteres; segunda ejecución sin cambios | Hecho |
| 7. Apartar el corpus de ejemplo | Solo los 27 archivos nuevos en `documentos/` | TecnoFábrica movido con `git mv` a `documentos/ejemplo_tecnofabrica/` | Hecho |
| 8. Conjunto de evaluación | Validador en verde y una fila por pregunta del banco | Validador listo: `scripts/validar_evaluacion.py`. **Falta** `datos/preguntas_evaluacion_green.csv` | Bloqueado: falta el banco de preguntas del PO |
| 9. Pruebas | `python -m pytest` en verde | **32 pruebas en verde**: generador (16), controles Gold (11) y validador de evaluación (5) | Hecho |
| 10. Entregar al LLM Engineer | LLM Engineer indexa sin fichas partidas | PR #2 abierto. Mensaje de entrega listo (sección 7) | En curso |

## 4. Hallazgos sobre el dato

1. **La advertencia sobre `main` del ETL ya no aplica.** Los planes dicen que `main` es una versión antigua (5 países). El 2026-11-23 el PR #1 del ETL integró `feat/airflow-medallion-alignment` en `main`; hoy ambos tienen exactamente los mismos archivos.
2. **El repo del ETL tiene otro nombre.** En GitHub es `AndreLopezRendon/Laboratorio-Apache-Airflow-`, no `Laboratorio-MLOps-green-data-etl` como dicen los planes.
3. **Distribución confirmada:** 6 Green, 5 Moderate y 9 Critical. China está exactamente en 0.10 y cuenta como Moderate.
4. **Un solo empate real:** Argentina y Brasil, ambos con 0.09. Australia y Francia (13.8 %) y Japón y México (7.1 %) coinciden solo al redondear; el ranking los ordena por el valor exacto y lo dice en el texto.
5. Los CSV traen `Renewable_Share` con todos los decimales de punto flotante (p. ej. `0.9090909090909091`); los documentos muestran porcentajes con un decimal, como pide la convención del equipo.

Ningún control falló, así que no hubo que reportar nada a quien mantiene el ETL.

## 5. Decisiones aplicadas

Las decisiones D1 a D7 siguen sin registro del Product Owner en `plan-equipo.md` §7. Según la regla del plan («si no se decide, se aplica la recomendación»), se aplicaron:

| Decisión | Aplicado |
|---|---|
| D1 Corpus | Datos verdes reemplazan a TecnoFábrica; el ejemplo queda en `documentos/ejemplo_tecnofabrica/` |
| D2 Idioma | Documentos en español, con el nombre original en inglés y alias |
| D4 Fuente | Snapshot de los CSV Gold (no Postgres) |
| D6 Agregación | Promedio simple de los países, dicho en cada resumen |

Decisiones técnicas propias:

| Decisión | Motivo |
|---|---|
| Ranking ordenado por el valor exacto; «empate» solo si el valor es idéntico | Ordenar por la cifra redondeada ponía a Australia antes que Francia aunque Francia es mayor |
| Fichas recortan primero la traducción de la región y luego los alias, nunca los números | Egipto y Estados Unidos no cabían en 500 caracteres con la plantilla completa |
| El generador solo reescribe archivos cuyo contenido cambió | Idempotencia verificable con `git status` |
| Validador de KPIs reconoce los nombres por palabras clave | `kpis.csv` usa nombres en inglés libres («Average Energy Consumption») |

## 6. Para el seguimiento del Scrum Master

| Tarea | Responsable | Estado al 2026-11-24 | Siguiente acción |
|---|---|---|---|
| Snapshot, controles, alias y corpus (pasos 1–7, 9) | Data Engineer | En revisión (PR #2) | Revisión y merge del PR #2 |
| Conjunto de evaluación (paso 8) | Data Engineer | Bloqueado | Requiere `datos/banco_preguntas.csv` del Product Owner |
| Registrar D1–D7 en `plan-equipo.md` §7 | Product Owner | Sin registrar | Confirmar o cambiar las recomendaciones aplicadas |
| Indexar el corpus y medir recuperación | LLM Engineer | Puede empezar tras el merge | `POST /indexar` debe devolver `"documentos": 27` |

Regla recomendada para el tablero: **desarrollado ≠ aceptado**. Estas tareas quedan en «En revisión» hasta el merge del PR #2 y la revisión del Product Owner.

Riesgos visibles:

- Sin el banco de preguntas no hay conjunto de evaluación, y sin él el LLM Engineer no puede calcular su línea base (sus pasos 5 y 6).
- La nota «commit inicial pendiente» de `plan-equipo.md` §8 está desactualizada: el repo ya tiene commits en `main`.

## 7. Mensaje de entrega al LLM Engineer

> Corpus listo en `feat/de-corpus-green` (PR #2). Snapshot del ETL `AndreLopezRendon/Laboratorio-Apache-Airflow-`, commit `aa4c813` (mismo árbol que `feat/airflow-medallion-alignment` `684fba9`); ver `datos/fuente/PROCEDENCIA.md`. Controles: 10 de 10 en PASS. 27 documentos en `documentos/`; `POST /indexar` debe devolver `"documentos": 27`. Todas las fichas de país tienen 500 caracteres o menos, así que con el chunker actual cada una queda en un solo fragmento. El conjunto de evaluación queda pendiente hasta tener el banco de preguntas.

## 8. Cómo reproducir

```powershell
git checkout feat/de-corpus-green
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install pytest
python -m pytest                       # 32 passed
python scripts\validar_gold.py         # 10 de 10 controles en PASS
python scripts\generar_documentos.py   # 27 documentos ... (0 con cambios)
```

## 9. Pendientes y límites

- Paso 8 (conjunto de evaluación), bloqueado por el banco de preguntas.
- La licencia del repo ETL y los términos de uso de los datos del World Bank siguen sin verificar (advertencia 6 de `plan-equipo.md`).
- Fuera del rol de Data Engineer: prompt, chunker y API (LLM Engineer); decisiones y metas de aceptación (Product Owner).
