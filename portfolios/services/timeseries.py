from __future__ import annotations

from decimal import Decimal
from datetime import date
from collections import defaultdict

# Selectors:
# - encapsulan queries a la base de datos
# - evitan SQL dentro del calculo del portafolio
from portfolios.selectors.holdings import initial_holdings_for_portfolio
from portfolios.selectors.trades import trades_for_portfolio
from portfolios.selectors.prices import prices_in_range, price_on_date


def portfolio_timeseries(*, portfolio_id: int, start: date, end: date) -> dict:

    # ------------------------------------------------------------------
    # 1) Holdings iniciales (estado base del portafolio en t0)
    # ------------------------------------------------------------------
    # Representan las cantidades iniciales de cada activo:
    # quantity_i = (peso_i * V0) / precio_i(t0)
    holdings_qs = list(initial_holdings_for_portfolio(portfolio_id=portfolio_id))

    if not holdings_qs:
        raise ValueError("Portfolio sin holdings iniciales (¿corriste el ETL?)")

    # Lista de activos del portafolio
    assets = [h.asset for h in holdings_qs]
    asset_ids = [a.id for a in assets]
    asset_codes = [a.code for a in assets]

    # Mapeo id
    id_to_code = {a.id: a.code for a in assets}

    # Cantidades base por activo (q_i en t0)
    base_qty = {h.asset_id: Decimal(h.quantity) for h in holdings_qs}

    # ------------------------------------------------------------------
    # 2) Trades (bonus del enunciado)
    # ------------------------------------------------------------------
    # Trades representan cambios en cantidades:
    # BUY  -> +delta_qty
    # SELL -> -delta_qty
    trades = list(trades_for_portfolio(portfolio_id=portfolio_id, start=None, end=end))

    # delta_qty_by_date_asset[(date, asset_id)] = cambio en cantidad
    # Usamos defaultdict para evitar inicializaciones manuales
    delta_qty_by_date_asset: dict[tuple[date, int], Decimal] = defaultdict(
        lambda: Decimal("0")
    )

    for tr in trades:
        # Precio del activo en la fecha del trade
        px = price_on_date(asset_id=tr.asset_id, dt=tr.date)

        # Si no hay precio, el trade no se puede aplicar
        if not px or Decimal(px.price) == 0:
            continue

        # amount_usd / price = cantidad transada
        delta = Decimal(tr.amount_usd) / Decimal(px.price)

        # SELL reduce cantidad
        if tr.side == "SELL":
            delta = -delta

        delta_qty_by_date_asset[(tr.date, tr.asset_id)] += delta

    # ------------------------------------------------------------------
    # 3) Precios historicos en el rango solicitado
    # ------------------------------------------------------------------
    prices = list(prices_in_range(asset_ids=asset_ids, start=start, end=end))
    prices_by_date: dict[date, dict[int, Decimal]] = defaultdict(dict)

    for pr in prices:
        prices_by_date[pr.date][pr.asset_id] = Decimal(pr.price)
        
    dates = sorted(prices_by_date.keys())

    # ------------------------------------------------------------------
    # serie temporal
    # ------------------------------------------------------------------
    current_qty = dict(base_qty)

    rows = []

    for dt in dates:
        # --------------------------------------------------------------
        # 4.1) Aplicar trades del día dt
        # --------------------------------------------------------------
        # Actualizamos cantidades:
        # q_{i,t} = q_{i,t-1} + delta_qty_{i,t}
        for aid in asset_ids:
            current_qty[aid] = current_qty.get(aid, Decimal("0")) + delta_qty_by_date_asset.get(
                (dt, aid), Decimal("0")
            )

        # --------------------------------------------------------------
        # 4.2) Calcular valores x_{i,t} y V_t
        # --------------------------------------------------------------
        x_by_asset = {}
        V = Decimal("0")

        for aid in asset_ids:
            px = prices_by_date[dt].get(aid)
            if px is None:
                continue

            # x_{i,t} = price_{i,t} * quantity_{i,t}
            x = px * current_qty.get(aid, Decimal("0"))
            x_by_asset[aid] = x
            V += x

        # --------------------------------------------------------------
        # 4.3) Calcular pesos w_{i,t}
        # --------------------------------------------------------------
        weights = {}

        if V != 0:
            # w_{i,t} = x_{i,t} / V_t
            for aid in asset_ids:
                x = x_by_asset.get(aid, Decimal("0"))
                weights[id_to_code[aid]] = float(x / V)
        else:
            # Caso defensivo: portafolio vacio
            for code in asset_codes:
                weights[code] = 0.0

        # --------------------------------------------------------------
        # 4.4) Agregar fila de la serie temporal
        # --------------------------------------------------------------
        rows.append(
            {
                "date": dt.isoformat(),
                "V": float(V),          # Valor total del portafolio en t
                "weights": weights,     # Pesos por activo en t
            }
        )

    # ------------------------------------------------------------------
    # 5) Respuesta final (contrato del endpoint)
    # ------------------------------------------------------------------
    return {
        "portfolio_id": portfolio_id,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "assets": asset_codes,
        "rows": rows,
    }
