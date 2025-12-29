from django.db import models

class DataImport(models.Model):
    source_name = models.CharField(max_length=255)          # p.ej. "datos.xlsx"
    file_hash = models.CharField(max_length=64, unique=True)
    imported_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="SUCCESS")  # SUCCESS/FAILED
    rows_inserted = models.IntegerField(default=0)
    rows_updated = models.IntegerField(default=0)
    notes = models.TextField(blank=True, default="")
