from django.db import models

class InitialHolding(models.Model):
    portfolio = models.ForeignKey("portfolios.Portfolio", on_delete=models.CASCADE)
    asset = models.ForeignKey("portfolios.Asset", on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=30, decimal_places=10)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["portfolio", "asset"], name="uq_holding_portfolio_asset")
        ]
