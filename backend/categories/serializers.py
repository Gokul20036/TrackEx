from rest_framework import serializers

class CategorySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
