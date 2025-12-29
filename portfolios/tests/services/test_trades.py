from datetime import date
from decimal import Decimal

from django.test import TestCase

from portfolios.models import Asset, Portfolio, Price, TradeLeg
from portfolios.services.trades import trade_create, TradeLegInput


class TradeCreateTests(TestCase):
    def setUp(self):
        self.asset_us = Asset.objects.create(code="US", name="United States")

        self.portfolio = Portfolio.objects.create(
            name="Portfolio 1",
            start_date=date(2022, 2, 15),
            initial_value=Decimal("1000000"),
        )

        Price.objects.create(
            asset=self.asset_us,
            date=date(2022, 5, 15),
            price=Decimal("100"),
        )

    def test_trade_is_created(self):
        legs = [
            TradeLegInput(
                asset_code="US",
                side="BUY",
                amount_usd=Decimal("100000"),
            )
        ]

        created = trade_create(
            portfolio_id=self.portfolio.id,
            dt=date(2022, 5, 15),
            legs=legs,
        )

        self.assertEqual(len(created), 1)
        self.assertEqual(TradeLeg.objects.count(), 1)
