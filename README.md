# Abaqus Test - Django + DRF

Backend en Django + DRF que calcula la serie temporal de un portafolio, ejecuta trades y expone una vista de graficos con assets estaticos locales.

## Stack
- Python 3.11+
- Django + Django REST Framework
- openpyxl

## Setup rapido
```bash
python -m venv .venv
# activar entorno
pip install -r requirements.txt
python manage.py migrate
```

## ETL (Excel -> BD)
Carga incremental e idempotente (hash del archivo). Se usa una transaccion atomica y logging para evitar estados a medias:
```bash
python manage.py load_datos_xlsx datos.xlsx          # salta si el hash ya fue importado
python manage.py load_datos_xlsx datos.xlsx --force  # reimporta y reemplaza holdings iniciales
```
Metricas basicas (assets/prices/holdings creados) quedan en `DataImport.notes`. Si algo falla se marca `status=FAILED` y se revierte toda la transaccion.

## Endpoints REST
- `GET /api/portfolios/<id>/timeseries/?start=YYYY-MM-DD&end=YYYY-MM-DD`
  - Valida `start <= end` y que `start` sea >= `portfolio.start_date`; si no, responde `400` con `{"start": ["fecha inicial no disponible"]}`.
  - Ejemplo: `curl "http://localhost:8000/api/portfolios/1/timeseries/?start=2022-02-15&end=2022-02-16"`

- `POST /api/portfolios/<id>/trades/`
  - Body:
    ```json
    {
      "date": "2022-05-15",
      "legs": [
        {"asset": "US", "side": "BUY", "amount_usd": "100000.00"}
      ]
    }
    ```
  - Antes de persistir un `SELL` calcula las cantidades actuales (holdings iniciales + trades previos convertidos por precio) y rechaza la operacion si deja el quantity en negativo: `{"legs": ["Cantidad insuficiente de US para vender; ..."]}`.

- `GET /api/imports/latest/`
  - Estado de la ultima importacion + metricas simples (`assets`, `prices`, `holdings`, `portfolios`).

## Vista de graficos
- `GET /portfolios/<id>/charts/?start=YYYY-MM-DD&end=YYYY-MM-DD`
- JavaScript y estilos movidos a `portfolios/static/portfolios/` (Bootstrap y Chart.js locales, sin depender de CDN). El fetch maneja errores de API y credenciales `same-origin`.

## Tests
```bash
python manage.py test
```
Incluyen pruebas de integracion para `PortfolioTimeseriesApi`, `PortfolioTradeCreateApi`, el endpoint de import status y la vista de graficos (verifican uso de assets estaticos).
