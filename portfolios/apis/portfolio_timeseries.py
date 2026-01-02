from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError, NotFound

from portfolios.models import Portfolio
from portfolios.services.timeseries import portfolio_timeseries


class PortfolioTimeseriesApi(APIView):
    class InputSerializer(serializers.Serializer):
        start = serializers.DateField()
        end = serializers.DateField()

        def validate(self, data):
            start, end = data["start"], data["end"]
            if start > end:
                raise ValidationError({"start": "el rango es invalido (start > end)"})

            portfolio: Portfolio | None = self.context.get("portfolio")
            if portfolio and start < portfolio.start_date:
                raise ValidationError({"start": "fecha inicial no disponible"})
            return data

    def get_portfolio(self, portfolio_id: int) -> Portfolio:
        portfolio = Portfolio.objects.filter(id=portfolio_id).first()
        if not portfolio:
            raise NotFound(f"Portfolio {portfolio_id} no existe")
        return portfolio

    def get(self, request, portfolio_id: int):
        portfolio = self.get_portfolio(portfolio_id)

        input_serializer = self.InputSerializer(
            data=request.query_params,
            context={"portfolio": portfolio},
        )
        input_serializer.is_valid(raise_exception=True)

        try:
            data = portfolio_timeseries(
                portfolio_id=portfolio_id,
                start=input_serializer.validated_data["start"],
                end=input_serializer.validated_data["end"],
            )
        except ValueError as exc:
            # Map domain errors to a 400 for clearer API responses
            raise ValidationError({"detail": str(exc)})

        return Response(data, status=status.HTTP_200_OK)
