from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status

from portfolios.apis.utils import inline_serializer
from portfolios.services.trades import trade_create, TradeLegInput


class PortfolioTradeCreateApi(APIView):
    class InputSerializer(serializers.Serializer):
        date = serializers.DateField()
        legs = inline_serializer(
            many=True,
            fields={
                "asset": serializers.CharField(),
                "side": serializers.ChoiceField(choices=["BUY", "SELL"]),
                "amount_usd": serializers.DecimalField(max_digits=20, decimal_places=2),
            },
        )

    class OutputSerializer(serializers.Serializer):
        created = serializers.IntegerField()

    def post(self, request, portfolio_id: int):
        input_serializer = self.InputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        legs = [
            TradeLegInput(
                asset_code=leg["asset"],
                side=leg["side"],
                amount_usd=leg["amount_usd"],
            )
            for leg in input_serializer.validated_data["legs"]
        ]

        created = trade_create(
            portfolio_id=portfolio_id,
            dt=input_serializer.validated_data["date"],
            legs=legs,
        )

        output_serializer = self.OutputSerializer({"created": len(created)})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
