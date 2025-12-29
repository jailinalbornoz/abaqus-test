from django.db import models

class Price(models.Model):
    asset = models.ForeignKey("portfolios.Asset", on_delete=models.CASCADE)
    date = models.DateField()
    price = models.DecimalField(max_digits=20, decimal_places=8)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["asset", "date"], name="uq_price_asset_date")
        ]
        indexes = [
            models.Index(fields=["asset", "date"]),
            models.Index(fields=["date"]),
        ]
