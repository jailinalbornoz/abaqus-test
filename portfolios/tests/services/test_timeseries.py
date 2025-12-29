from datetime import date
from decimal import Decimal

from django.test import TestCase

from portfolios.models import Asset, Portfolio, Price, InitialHolding
from portfolios.services.timeseries import portfolio_timeseries


class PortfolioTimeseriesTests(TestCase):
    def setUp(self):
        # 1) Crear assets
        self.asset_us = Asset.objects.create(code="US", name="United States")
        self.asset_eu = Asset.objects.create(code="EU", name="Europe")

        # 2) Crear portfolio
        self.portfolio = Portfolio.objects.create(
            name="Portfolio 1",
            start_date=date(2022, 2, 15),
            initial_value=Decimal("1000000"),
        )

        # 3) Crear precios (2 días)
        Price.objects.create(asset=self.asset_us, date=date(2022, 2, 15), price=Decimal("100"))
        Price.objects.create(asset=self.asset_eu, date=date(2022, 2, 15), price=Decimal("200"))

        Price.objects.create(asset=self.asset_us, date=date(2022, 2, 16), price=Decimal("110"))
        Price.objects.create(asset=self.asset_eu, date=date(2022, 2, 16), price=Decimal("190"))

        # 4) Crear holdings iniciales
        InitialHolding.objects.create(
            portfolio=self.portfolio,
            asset=self.asset_us,
            quantity=Decimal("5000"),
        )
        InitialHolding.objects.create(
            portfolio=self.portfolio,
            asset=self.asset_eu,
            quantity=Decimal("2500"),
        )

    def test_timeseries_returns_values_and_weights(self):
        result = portfolio_timeseries(
            portfolio_id=self.portfolio.id,
            start=date(2022, 2, 15),
            end=date(2022, 2, 16),
        )

        # 1) Hay filas
        self.assertTrue(len(result["rows"]) > 0)

        # 2) Revisar una fila
        row = result["rows"][0]

        self.assertIn("V", row)
        self.assertIn("weights", row)

        # 3) Los pesos suman ~1
        total_weight = sum(row["weights"].values())
        self.assertAlmostEqual(total_weight, 1.0, places=6)
