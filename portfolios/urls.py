from django.urls import path

from portfolios.views.home import HomeView
from portfolios.apis.portfolio_timeseries import PortfolioTimeseriesApi
from portfolios.apis.portfolio_trades import PortfolioTradeCreateApi
from portfolios.apis.import_status import LatestImportStatusApi
from portfolios.views.charts import PortfolioChartsView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("api/portfolios/<int:portfolio_id>/timeseries/", PortfolioTimeseriesApi.as_view()),
    path("api/portfolios/<int:portfolio_id>/trades/", PortfolioTradeCreateApi.as_view()),
    path("api/imports/latest/", LatestImportStatusApi.as_view()),
    path("portfolios/<int:portfolio_id>/charts/", PortfolioChartsView.as_view()),
]
