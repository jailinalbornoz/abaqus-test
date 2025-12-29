# Abaqus Test — Django Backend

Backend en **Django + DRF** para calcular la evolución del valor de un portafolio de inversión y los pesos por activo a partir de un archivo Excel con **weights** y **precios**. Incluye ejecución de trades y visualización básica.

## Stack
- Python 3.11+
- Django
- Django REST Framework
- openpyxl

## Setup rápido
```bash
python -m venv .venv
# activar entorno
pip install -r requirements.txt
python manage.py migrate
```


## Carga de datos (ETL)
ETL incremental e idempotente desde Excel.
```bash
python manage.py load_datos_xlsx datos.xlsx

## API principal
GET /api/portfolios/<id>/timeseries/?start=YYYY-MM-DD&end=YYYY-MM-DD

## Trades
POST /api/portfolios/<id>/trades/

## Gráficos:
GET /portfolios/<id>/charts/?start=YYYY-MM-DD&end=YYYY-MM-DD


## Tests

python manage.py test
