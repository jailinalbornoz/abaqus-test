from datetime import date
from portfolios.models import TradeLeg

def trades_for_portfolio(*, portfolio_id: int, start: date | None = None, end: date | None = None):
    qs = TradeLeg.objects.filter(portfolio_id=portfolio_id).select_related("asset")
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)
    return qs.order_by("date", "id")
