from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from portfolios.services.etl import import_datos_xlsx


class Command(BaseCommand):
    help = "Importa datos desde un XLSX (weights + Precios) de forma incremental e idempotente."

    def add_arguments(self, parser):
        parser.add_argument("path", type=str)
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--start-date", type=str, default="2022-02-15")
        parser.add_argument("--v0", type=str, default="1000000000")

    def handle(self, *args, **options):
        path = options["path"]
        force = options["force"]

        try:
            start_date = datetime.strptime(options["start_date"], "%Y-%m-%d").date()
        except ValueError as e:
            raise CommandError("start-date debe ser YYYY-MM-DD") from e

        v0 = Decimal(options["v0"])

        data_import = import_datos_xlsx(path=path, start_date=start_date, v0=v0, force=force)

        self.stdout.write(
            self.style.SUCCESS(
                f"Import OK: {data_import.source_name} inserted={data_import.rows_inserted} updated={data_import.rows_updated}"
            )
        )
