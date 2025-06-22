from rest_framework import serializers

class StockPredictionSerializer(serializers.Serializer):
    ticker = serializers.CharField()
    last_date = serializers.CharField()
    next_business_day = serializers.CharField()
    current_price = serializers.FloatField()
    predicted_price = serializers.FloatField()
    error = serializers.CharField(required=False, allow_blank=True)
