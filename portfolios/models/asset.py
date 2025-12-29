from django.db import models

class Asset(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255, blank=True, default="")

    def __str__(self) -> str:
        return self.code
