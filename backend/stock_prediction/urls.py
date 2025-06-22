# prediction_app/urls.py

from django.urls import path
from .views import  predict_stocks_by_investment

urlpatterns = [
    # This URL pattern will route requests to your StockPredictionAPIView.
    # For example, a request to `/api/stock_prediction/?ticker=AAPL` will be handled here.
    path('', predict_stocks_by_investment, name='multi_stock_prediction'),
]
