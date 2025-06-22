import datetime
from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

def get_user_id_from_token(request):
    """
    Extracts and validates the token from the request.
    Returns a tuple: (user_id, error_response). If token is valid, error_response is None.
    """
    token = request.headers.get('Authorization') or request.GET.get('token') or request.data.get('token')
    if not token:
        return None, Response({"error": "Token is required."}, status=status.HTTP_400_BAD_REQUEST)
    if token.startswith("Bearer "):
        token = token[7:]
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id FROM user_token WHERE token = %s", [token])
            user_token = cursor.fetchone()
        if not user_token:
            return None, Response({"error": "Invalid token."}, status=status.HTTP_401_UNAUTHORIZED)
        return user_token[0], None
    except Exception as e:
        return None, Response({"error": f"Token validation error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_budget_by_category(request):
    """
    Retrieves the budget for a given category for the authenticated user.
    Expects:
      - Token (in the Authorization header or as a query parameter 'token')
      - category_name (as a query parameter)
    """
    user_id, error_response = get_user_id_from_token(request)
    if error_response:
        return error_response

    category_name = request.query_params.get('category_name')
    if not category_name:
        return Response({"error": "Parameter 'category_name' is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT cat.budget
                FROM categorize cat
                INNER JOIN categories c ON cat.category_id = c.category_id
                WHERE c.name = %s AND cat.user_id = %s
            """
            cursor.execute(sql, [category_name, user_id])
            result = cursor.fetchone()
        if result is not None:
            return Response({"budget": result[0]}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "No budget found for the given category and user."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def insert_budget_by_category(request):
    """
    Inserts a new budget entry into the categorize table for the authenticated user.
    Expects:
      - Token (in the Authorization header or in the request data as 'token')
      - category_name (in request data)
      - budget (in request data)
    """
    user_id, error_response = get_user_id_from_token(request)
    if error_response:
        return error_response

    category_name = request.data.get('category_name')
    budget = request.data.get('budget')
    if not category_name or budget is None:
        return Response({"error": "Both 'category_name' and 'budget' are required."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT category_id FROM categories WHERE name = %s", [category_name])
            category_result = cursor.fetchone()
            if not category_result:
                return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
            category_id = category_result[0]
            insert_sql = """
                INSERT INTO categorize (user_id, category_id, budget)
                VALUES (%s, %s, %s)
            """
            cursor.execute(insert_sql, [user_id, category_id, budget])
        return Response({"message": "Budget inserted successfully."}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": f"An error occurred while inserting the budget: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def update_budget_by_category(request):
    """
    Updates an existing budget for a given category for the authenticated user.
    Expects:
      - Token (in the Authorization header or in the request data as 'token')
      - category_name (in request data)
      - budget (in request data)
    """
    user_id, error_response = get_user_id_from_token(request)
    if error_response:
        return error_response

    category_name = request.data.get('category_name')
    budget = request.data.get('budget')
    if not category_name or budget is None:
        return Response({"error": "Both 'category_name' and 'budget' are required."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT category_id FROM categories WHERE name = %s", [category_name])
            category_result = cursor.fetchone()
            if not category_result:
                return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
            category_id = category_result[0]
            update_sql = """
                UPDATE categorize
                SET budget = %s
                WHERE user_id = %s AND category_id = %s
            """
            cursor.execute(update_sql, [budget, user_id, category_id])
        return Response({"message": "Budget updated successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": f"An error occurred while updating the budget: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_expense_for_category_current_month(request):
    """
    Retrieves all expenses for a given category for the current month for the authenticated user.
    Expects:
      - Token (in the Authorization header or as a query parameter 'token')
      - category_name (as a query parameter)
    """
    user_id, error_response = get_user_id_from_token(request)
    if error_response:
        return error_response

    category_name = request.query_params.get('category_name')
    if not category_name:
        return Response({"error": "Parameter 'category_name' is required."}, status=status.HTTP_400_BAD_REQUEST)

    now = datetime.datetime.now()
    current_month = now.month
    current_year = now.year

    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT expense_id, amount, date, payment_method, description
                FROM expense
                WHERE user_id = %s
                  AND category_id = (SELECT category_id FROM categories WHERE name = %s)
                  AND MONTH(date) = %s AND YEAR(date) = %s
            """
            cursor.execute(sql, [user_id, category_name, current_month, current_year])
            rows = cursor.fetchall()
        expenses = []
        for row in rows:
            expenses.append({
                "expense_id": row[0],
                "amount": row[1],
                "date": row[2],
                "payment_method": row[3],
                "description": row[4]
            })
        return Response({"expenses": expenses}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
