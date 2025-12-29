from django.db import models

class TradeLeg(models.Model):
    BUY = "BUY"
    SELL = "SELL"
    SIDE_CHOICES = [(BUY, "BUY"), (SELL, "SELL")]

    portfolio = models.ForeignKey("portfolios.Portfolio", on_delete=models.CASCADE)
    date = models.DateField()
    asset = models.ForeignKey("portfolios.Asset", on_delete=models.CASCADE)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    amount_usd = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=["portfolio", "date"]),
            models.Index(fields=["date"]),
        ]
