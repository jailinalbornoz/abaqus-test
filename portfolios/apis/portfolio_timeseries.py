from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status

from portfolios.services.timeseries import portfolio_timeseries


class PortfolioTimeseriesApi(APIView):
    class InputSerializer(serializers.Serializer):
        start = serializers.DateField()
        end = serializers.DateField()

    def get(self, request, portfolio_id: int):
        input_serializer = self.InputSerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)

        data = portfolio_timeseries(
            portfolio_id=portfolio_id,
            start=input_serializer.validated_data["start"],
            end=input_serializer.validated_data["end"],
        )
        return Response(data, status=status.HTTP_200_OK)
