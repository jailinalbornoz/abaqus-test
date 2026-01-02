from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from datetime import date

from django.db import transaction
from django.core.exceptions import ValidationError

from portfolios.models import TradeLeg, Asset
from portfolios.selectors.prices import price_on_date
from portfolios.selectors.holdings import initial_holdings_for_portfolio
from portfolios.selectors.trades import trades_for_portfolio


# ---------------------------------------------------------------------
# Input del trade
# ---------------------------------------------------------------------
# No es un modelo de base de datos, sino una estructura de entrada validada previamente por el serializer / API.

# Conceptualmente:
# - asset_code: activo sobre el que se opera
# - side: BUY o SELL
# - amount_usd: monto en usd (no cantidad)

@dataclass(frozen=True)
class TradeLegInput:
    asset_code: str
    side: str
    amount_usd: Decimal


# ---------------------------------------------------------------------
# Creacion de trades (logica de negocio)
# ---------------------------------------------------------------------
def _current_quantities(*, portfolio_id: int, up_to_dt: date) -> dict[int, Decimal]:
    """
    Cantidades actuales por asset calculadas a partir de holdings iniciales
    y trades ya persistidos hasta la fecha indicada (inclusive).
    """
    quantities: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))

    for holding in initial_holdings_for_portfolio(portfolio_id=portfolio_id):
        quantities[holding.asset_id] += Decimal(holding.quantity)

    for tr in trades_for_portfolio(portfolio_id=portfolio_id, end=up_to_dt):
        px = price_on_date(asset_id=tr.asset_id, dt=tr.date)
        if not px or Decimal(px.price) == 0:
            continue
        delta = Decimal(tr.amount_usd) / Decimal(px.price)
        if tr.side == TradeLeg.SELL:
            delta = -delta
        quantities[tr.asset_id] += delta

    return quantities


@transaction.atomic
def trade_create(
    *,
    portfolio_id: int,
    dt: date,
    legs: list[TradeLegInput],
) -> list[TradeLeg]:
    """
    Crea uno o mas TradeLegs para un portafolio en una fecha dada.

    Reglas clave:
    - Cada leg representa una operacion independiente
    - El impacto real en el portafolio se calcula luego, al reconstruir la serie temporal (no aqui)
    - La funcion es atomica: o se crean todos los legs o ninguno
    """

    created: list[TradeLeg] = []
    quantities = _current_quantities(portfolio_id=portfolio_id, up_to_dt=dt)

    for leg in legs:
        asset = Asset.objects.filter(code=leg.asset_code).first()
        if not asset:
            raise ValidationError(f"Asset no existe: {leg.asset_code}")
        px = price_on_date(asset_id=asset.id, dt=dt)
        if not px or px.price == 0:
            raise ValidationError(f"No hay precio para {leg.asset_code} en {dt}")

        # amount_usd / price = cantidad transada
        delta_qty = Decimal(leg.amount_usd) / Decimal(px.price)

        if leg.side == TradeLeg.SELL:
            available = quantities.get(asset.id, Decimal("0"))
            new_qty = available - delta_qty
            if new_qty < 0:
                raise ValidationError(
                    {"legs": f"Cantidad insuficiente de {asset.code} para vender; disponible={available}, solicitado={delta_qty}"}
                )
            quantities[asset.id] = new_qty
        else:
            quantities[asset.id] = quantities.get(asset.id, Decimal("0")) + delta_qty

        created.append(
            TradeLeg.objects.create(
                portfolio_id=portfolio_id,
                date=dt,
                asset=asset,
                side=leg.side,
                amount_usd=leg.amount_usd,
            )
        )
    return created
