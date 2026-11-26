# Procedencia del snapshot Gold

| Campo | Valor |
|---|---|
| Repo de origen | https://github.com/AndreLopezRendon/Laboratorio-Apache-Airflow- (el ETL Green Data; en los planes aparece como `Laboratorio-MLOps-green-data-etl`) |
| Copia local usada | `C:\Airflow\Laboratorio-Apache-Airflow-` |
| Rama del clon local | `main` |
| Commit | `aa4c813818344b8c773f79811b3a458e3916b45f` (merge del PR #1, 2026-11-23) |
| Rama recomendada (D4) | `feat/airflow-medallion-alignment`, commit `684fba9829b4ec9625cfae5690ca5cd4e9e1d95d` |
| Fecha de copia | 2026-11-24 |
| Copiado por | Majo (Data Engineer) |

## Por qué `main` sirve en este caso

Los planes advierten que `main` era una versión antigua (5 países, `Emission_Efficiency`). Eso cambió: el PR #1 integró `feat/airflow-medallion-alignment` en `main` y los dos commits tienen **el mismo árbol de archivos**. Los blobs de los dos CSV son idénticos en ambos:

| Archivo en el ETL | Copia aquí | Blob git | SHA-256 de la copia |
|---|---|---|---|
| `data/gold/gold_final.csv` | `datos/fuente/gold_final.csv` | `38a5d6d99a56dca570d7a5a2ed2f3c57069f5b41` | `0b17b1d70959b4a49d7f6031b5e9491445bc3365d128702397b095fdc263705e` |
| `reports/kpis.csv` | `datos/fuente/kpis.csv` | `492b34314a26d7d983f08cc03f4aa3d8875e5dc5` | `c49f4fb822bd5b816a134dbd2b547cb7bd48d601f27826db4c0b0fdf49bb985d` |

Las copias se tomaron del commit, con saltos de línea LF. En el clon de Windows los archivos tienen CRLF por `core.autocrlf`; el contenido es el mismo.

## Cómo reproducirlo

```powershell
$ETL = "C:\Airflow\Laboratorio-Apache-Airflow-"
git -C $ETL fetch origin
git -C $ETL show aa4c813:data/gold/gold_final.csv > datos\fuente\gold_final.csv
git -C $ETL show aa4c813:reports/kpis.csv > datos\fuente\kpis.csv
python scripts\validar_gold.py
```

Ojo: en PowerShell 5, `>` escribe UTF-16. Usa PowerShell 7 o `git -C $ETL show ... | Set-Content -Encoding utf8NoBOM ...`.

Son datos de laboratorio, no estadísticas oficiales. El repo ETL no tiene LICENSE (plan-equipo, advertencia 6).
