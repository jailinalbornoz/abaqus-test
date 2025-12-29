from django.db import models

class Portfolio(models.Model):
    name = models.CharField(max_length=100, unique=True)
    start_date = models.DateField()
    initial_value = models.DecimalField(max_digits=20, decimal_places=2)

    def __str__(self) -> str:
        return self.name
