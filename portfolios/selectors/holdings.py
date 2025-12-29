from portfolios.models import InitialHolding

def initial_holdings_for_portfolio(*, portfolio_id: int):
    return (
        InitialHolding.objects
        .filter(portfolio_id=portfolio_id)
        .select_related("asset")
        .order_by("asset__code")
    )
