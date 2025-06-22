from rest_framework import serializers
from .models import Payment

class CreateOrderSerializer(serializers.Serializer):
    amount = serializers.FloatField()
    category = serializers.CharField(required=False)
    upi_id = serializers.CharField(required=False, allow_blank=True)
    mobile_number = serializers.CharField(required=False, allow_blank=True)

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'