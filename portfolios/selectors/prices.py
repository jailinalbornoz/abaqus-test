from datetime import date
from portfolios.models import Price

def prices_in_range(*, asset_ids: list[int], start: date, end: date):
    return (
        Price.objects
        .filter(asset_id__in=asset_ids, date__gte=start, date__lte=end)
        .order_by("date")
        .select_related("asset")
    )

def price_on_date(*, asset_id: int, dt: date):
    return Price.objects.filter(asset_id=asset_id, date=dt).first()
