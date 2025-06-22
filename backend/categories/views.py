from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import CategorySerializer

@api_view(['GET'])
def get_categories(request):
    """
    Retrieves all categories from the categories table using raw SQL.
    """
    try:
        with connection.cursor() as cursor:
            query = "SELECT name FROM categories"
            cursor.execute(query)
            rows = cursor.fetchall()
            # Convert list of tuples (each containing one value) into a list of dicts.
            categories = [{'name': row[0]} for row in rows]
        
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
