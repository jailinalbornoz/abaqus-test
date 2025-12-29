from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import date

from django.db import transaction
from django.core.exceptions import ValidationError

from portfolios.models import TradeLeg, Asset
from portfolios.selectors.prices import price_on_date


# ---------------------------------------------------------------------
# Input del trade
# ---------------------------------------------------------------------
# No es un modelo de base de datos, sino una estructura de entrada
# validada previamente por el serializer / API.
#
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
@transaction.atomic
def trade_create(*, portfolio_id: int, dt: date, legs: list[TradeLegInput]) -> list[TradeLeg]:
    """
    Crea uno o mas TradeLegs para un portafolio en una fecha dada.

    Reglas clave:
    - Cada leg representa una operacion independiente
    - El impacto real en el portafolio se calcula luego, al reconstruir la serie temporal (no aqui)
    - La funcion es atomica: o se crean todos los legs o ninguno
    """

    created: list[TradeLeg] = []

    for leg in legs:
        asset = Asset.objects.filter(code=leg.asset_code).first()
        if not asset:
            raise ValidationError(f"Asset no existe: {leg.asset_code}")
        px = price_on_date(asset_id=asset.id, dt=dt)
        if not px or px.price == 0:
            raise ValidationError(f"No hay precio para {leg.asset_code} en {dt}")
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
