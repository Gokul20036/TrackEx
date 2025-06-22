from rest_framework.decorators import api_view
from rest_framework.response import Response
from .predict_next_day import predict_next_day_price_new
from .serializers import StockPredictionSerializer

@api_view(['POST'])
def predict_stocks_by_investment(request):
    """
    Expects a JSON payload like:
    {
       "tickers": ["RELIANCE.NS", "TCS.NS", "SBIN.NS", ...],
       "investment_amount": 1500.0
    }
    For each ticker, this endpoint predicts the next business day's price.
    It returns predictions under two headings:
      - "recommended_stocks": stocks where current_price <= investment_amount and predicted_price > current_price.
      - "other_stocks": all other stocks (including errors).
    """
    tickers = request.data.get("tickers", [])
    investment_amount = request.data.get("investment_amount")
    
    if not tickers:
        return Response({"error": "Tickers not provided."}, status=400)
    if investment_amount is None:
        return Response({"error": "Investment amount not provided."}, status=400)
    
    try:
        investment_amount = float(investment_amount)
    except ValueError:
        return Response({"error": "Invalid investment amount."}, status=400)
    
    recommended = []
    others = []
    
    # Define the required fields and their default values.
    required_fields_defaults = {
        "ticker": lambda t: t.upper(),
        "last_date": lambda: "",
        "next_business_day": lambda: "",
        "current_price": lambda: 0.0,
        "predicted_price": lambda: 0.0,
    }
    
    for ticker in tickers:
        prediction = predict_next_day_price_new(ticker)
        prediction = dict(prediction)
        
        # Ensure all required fields exist.
        for field, default_func in required_fields_defaults.items():
            if field not in prediction:
                prediction[field] = default_func(ticker) if field == "ticker" else default_func()
        
        # Categorize predictions.
        if "error" in prediction:
            others.append(prediction)
        else:
            current_price = prediction.get("current_price", float('inf'))
            predicted_price = prediction.get("predicted_price", 0)
            if current_price <= investment_amount and predicted_price > current_price:
                recommended.append(prediction)
            else:
                others.append(prediction)
    
    serializer_recommended = StockPredictionSerializer(recommended, many=True)
    serializer_others = StockPredictionSerializer(others, many=True)
    
    response_data = {
        "recommended_stocks": serializer_recommended.data,
        "other_stocks": serializer_others.data
    }
    
    return Response(response_data)
