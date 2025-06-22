from rest_framework import serializers

class ExpenseInputSerializer(serializers.Serializer):
    category_name = serializers.CharField(max_length=100)
    category_description = serializers.CharField(max_length=255)  # New field for description
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    date = serializers.DateField()
    payment_method = serializers.CharField(max_length=100)  # Ensure payment_method is also captured

class ExpenseOutputSerializer(serializers.Serializer):
    category = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=255)  # Added description in the output
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    date = serializers.DateField()
