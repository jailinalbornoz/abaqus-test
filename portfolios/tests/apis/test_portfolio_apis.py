from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from portfolios.models import (
    Asset,
    DataImport,
    InitialHolding,
    Portfolio,
    Price,
    TradeLeg,
)


class PortfolioApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.asset_us = Asset.objects.create(code="US", name="United States")
        self.portfolio = Portfolio.objects.create(
            name="Portfolio 1",
            start_date=date(2022, 2, 15),
            initial_value=Decimal("1000000"),
        )
        InitialHolding.objects.create(
            portfolio=self.portfolio,
            asset=self.asset_us,
            quantity=Decimal("10"),
        )
        Price.objects.create(
            asset=self.asset_us,
            date=date(2022, 2, 15),
            price=Decimal("100"),
        )
        Price.objects.create(
            asset=self.asset_us,
            date=date(2022, 2, 16),
            price=Decimal("110"),
        )

    def test_timeseries_returns_data(self):
        resp = self.client.get(
            f"/api/portfolios/{self.portfolio.id}/timeseries/",
            {"start": "2022-02-15", "end": "2022-02-16"},
        )

        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIn("rows", payload)
        self.assertGreater(len(payload["rows"]), 0)
        self.assertIn("assets", payload)
        self.assertIn("V", payload["rows"][0])

    def test_timeseries_rejects_start_before_launch(self):
        resp = self.client.get(
            f"/api/portfolios/{self.portfolio.id}/timeseries/",
            {"start": "2022-01-01", "end": "2022-02-16"},
        )

        self.assertEqual(resp.status_code, 400)
        self.assertIn("fecha inicial no disponible", str(resp.json()))

    def test_trade_rejects_sell_without_liquidity(self):
        resp = self.client.post(
            f"/api/portfolios/{self.portfolio.id}/trades/",
            {
                "date": "2022-02-15",
                "legs": [
                    {"asset": "US", "side": TradeLeg.SELL, "amount_usd": "2000.00"}
                ],
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(TradeLeg.objects.count(), 0)
        self.assertIn("Cantidad insuficiente", str(resp.json()))

    def test_trade_creates_leg(self):
        resp = self.client.post(
            f"/api/portfolios/{self.portfolio.id}/trades/",
            {
                "date": "2022-02-15",
                "legs": [
                    {"asset": "US", "side": TradeLeg.BUY, "amount_usd": "500.00"}
                ],
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json().get("created"), 1)
        self.assertEqual(TradeLeg.objects.count(), 1)

    def test_latest_import_status_endpoint(self):
        DataImport.objects.create(
            source_name="datos.xlsx",
            file_hash="abc123",
            status="SUCCESS",
            rows_inserted=10,
            rows_updated=0,
            notes="test",
        )

        resp = self.client.get("/api/imports/latest/")

        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(payload["source_name"], "datos.xlsx")
        self.assertIn("assets", payload)
        self.assertIn("prices", payload)
