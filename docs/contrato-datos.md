# Contrato de datos — snapshot Gold de Green Data

> Dueño: Data Engineer. Implementado en [`scripts/validar_gold.py`](../scripts/validar_gold.py). Contexto en [plan-equipo.md §3](plan-equipo.md#3-contexto-del-dataset).

## Origen

| Campo | Valor |
|---|---|
| Repo de origen | `AndreLopezRendon/Laboratorio-Apache-Airflow-` (el ETL Green Data, solo lectura) |
| Rama | `feat/airflow-medallion-alignment` (decisión D4). Desde el PR #1 del ETL, `main` tiene el mismo contenido |
| Archivos | `data/gold/gold_final.csv` y `reports/kpis.csv` |
| Copia en este repo | `datos/fuente/` (ver `datos/fuente/PROCEDENCIA.md` para el commit exacto) |

Son **datos de laboratorio**, no estadísticas oficiales, y no documentan unidad ni año.

## Esquema de `gold_final.csv`

Una fila por país. Las 12 columnas deben venir con estos nombres y en este orden.

| # | Columna | Tipo | Nulos | Rango / dominio | Significado |
|---|---|---|---|---|---|
| 1 | `Country` | texto | no | nombre del World Bank en inglés | País (p. ej. `Egypt, Arab Rep.`) |
| 2 | `Country_Code` | texto | no | 3 letras mayúsculas, único | ISO3, clave del dataset |
| 3 | `Capital_City` | texto | no | en inglés, sin tildes | Capital |
| 4 | `Region` | texto | no | regiones del World Bank | Región |
| 5 | `Income_Level` | texto | no | High / Upper middle / Lower middle income | Nivel de ingreso |
| 6 | `Longitude` | decimal | no | −180 a 180 | Longitud de la capital |
| 7 | `Latitude` | decimal | no | −90 a 90 | Latitud de la capital |
| 8 | `Energy_Consumption` | decimal | no | > 0 | Consumo de energía (sin unidad ni año) |
| 9 | `Renewable_Energy` | decimal | no | ≥ 0 y ≤ `Energy_Consumption` | Energía renovable (misma unidad, supuesta) |
| 10 | `Energy_per_Renewable_Unit` | decimal | no | `Energy_Consumption / (Renewable_Energy + 1)` | Razón consumo / renovable. **No mide emisiones** |
| 11 | `Renewable_Share` | decimal | no | 0 a 1, `Renewable_Energy / Energy_Consumption` | Participación renovable |
| 12 | `Environmental_Status` | texto | no | `Green` / `Moderate` / `Critical` / `Unknown` | Estado según umbrales del laboratorio |

## Esquema de `kpis.csv`

7 KPIs: total de países, consumo promedio, consumo máximo, consumo mínimo, energía renovable promedio, cantidad de `Green` y cantidad de `Critical`. El validador acepta formato largo (una fila por KPI: nombre, valor) o ancho (una fila, una columna por KPI) y reconoce los nombres por palabras clave (`PATRONES_KPI` en el script).

## Controles

`python scripts/validar_gold.py` imprime `PASS` o `FAIL` por control y termina con código 1 si alguno falla.

| # | Control | Tolerancia |
|---|---|---|
| C1 | Las 12 columnas existen, con esos nombres y en ese orden | exacto |
| C2 | Número de filas = 20 (`--filas-esperadas` para cambiarlo) | exacto |
| C3 | `Country_Code` único y de 3 letras mayúsculas | exacto |
| C4 | Ninguna celda vacía | exacto |
| C5 | `Energy_Consumption` > 0 y `Renewable_Energy` ≥ 0, ambos numéricos | exacto |
| C6 | `Renewable_Energy` ≤ `Energy_Consumption` | exacto |
| C7 | `Renewable_Share` en [0, 1] y coherente con `Renewable_Energy / Energy_Consumption` | ± 0.006 (admite redondeo a 2 decimales) |
| C8 | `Energy_per_Renewable_Unit` coherente con `Energy_Consumption / (Renewable_Energy + 1)` | 1 % relativo o 0.01 |
| C9 | `Environmental_Status` según `Renewable_Share`: ≥ 0.30 Green, ≥ 0.10 Moderate, < 0.10 Critical. También avisa si el cociente exacto cae del otro lado de una frontera | exacto en la frontera (0.10 es Moderate) |
| C10 | Los KPIs coinciden con lo calculado desde el Gold | 0.1 % relativo o 0.01 |

Si un control falla, **no se corrige en silencio**: se reporta con la evidencia a quien mantiene el ETL y se anota abajo.

## Última ejecución

| Fecha | Commit del ETL | Resultado | Observaciones |
|---|---|---|---|
| 2026-11-24 | `aa4c813` (= árbol de `684fba9`) | 10 de 10 en PASS | 20 países: 6 Green, 5 Moderate, 9 Critical. China en 0.10 exacto (Moderate). Empate exacto Argentina y Brasil en 0.09 |

## Hallazgos reportados

Ningún control falló. Observaciones para el equipo, sin acción requerida en el ETL:

- `Renewable_Share` y `Energy_per_Renewable_Unit` vienen con todos los decimales de punto flotante (p. ej. `0.9090909090909091`). Los documentos los redondean a un decimal en porcentaje.
- Australia (0.1375) y Francia (0.1385) dan 13.8 % al redondear, igual que Japón (0.0706) y México (0.0714) dan 7.1 %. No son empates: el ranking los ordena por el valor exacto y lo dice en el texto.
- El nombre del repo ETL en GitHub es `Laboratorio-Apache-Airflow-`, no `Laboratorio-MLOps-green-data-etl` como dicen los planes.
