from datetime import date
from decimal import Decimal

from django.test import Client, TestCase

from portfolios.models import Portfolio


class ChartsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.portfolio = Portfolio.objects.create(
            name="Charts Portfolio",
            start_date=date(2022, 2, 15),
            initial_value=Decimal("1000000"),
        )

    def test_charts_template_uses_static_assets(self):
        resp = self.client.get(f"/portfolios/{self.portfolio.id}/charts/")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("portfolios/js/chart.umd.min.js", html)
        self.assertIn("portfolios/js/charts.js", html)
        self.assertIn("portfolios/css/charts.css", html)
