from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from portfolios.models import (
    Asset,
    DataImport,
    InitialHolding,
    Portfolio,
    Price,
)


class LatestImportStatusApi(APIView):
    class OutputSerializer(serializers.Serializer):
        source_name = serializers.CharField()
        file_hash = serializers.CharField()
        status = serializers.CharField()
        imported_at = serializers.DateTimeField()
        rows_inserted = serializers.IntegerField()
        rows_updated = serializers.IntegerField()
        notes = serializers.CharField(allow_blank=True)
        assets = serializers.IntegerField()
        prices = serializers.IntegerField()
        holdings = serializers.IntegerField()
        portfolios = serializers.IntegerField()

    def get(self, request):
        latest = DataImport.objects.order_by("-imported_at").first()
        if not latest:
            return Response(
                {"detail": "No hay importaciones registradas"},
                status=status.HTTP_404_NOT_FOUND,
            )

        metrics = {
            "assets": Asset.objects.count(),
            "prices": Price.objects.count(),
            "holdings": InitialHolding.objects.count(),
            "portfolios": Portfolio.objects.count(),
        }

        payload = {
            "source_name": latest.source_name,
            "file_hash": latest.file_hash,
            "status": latest.status,
            "imported_at": latest.imported_at,
            "rows_inserted": latest.rows_inserted,
            "rows_updated": latest.rows_updated,
            "notes": latest.notes,
            **metrics,
        }

        serializer = self.OutputSerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)
