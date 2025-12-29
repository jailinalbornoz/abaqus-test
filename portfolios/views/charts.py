from django.views.generic import TemplateView

class PortfolioChartsView(TemplateView):
    template_name = "portfolios/charts.html"
