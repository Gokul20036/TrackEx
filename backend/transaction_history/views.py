from datetime import datetime
from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Utility function to execute SQL queries.
def execute_query(query, params=None, fetch_one=False):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        if fetch_one:
            return cursor.fetchone()
        return None

@api_view(['GET'])
def get_expenses(request):
    """
    Retrieves expenses for the authenticated user.
    Optional query parameters:
      - start_date (YYYY-MM-DD)
      - end_date (YYYY-MM-DD)
      - category (e.g., "Food", "Groceries", etc.; use 'All' for no filter)
    """
    token = request.headers.get('Authorization') or request.GET.get('token')
    if not token:
        return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
    if token.startswith("Bearer "):
        token = token[7:]
    
    try:
        # Validate token and get user_id.
        user_token = execute_query("SELECT user_id FROM user_token WHERE token = %s", [token], fetch_one=True)
        if not user_token:
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
        user_id = user_token[0]

        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        category = request.GET.get("category")
        
        # Build dynamic SQL conditions.
        conditions = ["e.user_id = %s"]
        params = [user_id]
        if start_date:
            conditions.append("DATE(e.date) >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(e.date) <= %s")
            params.append(end_date)
        if category and category.lower() != "all":
            conditions.append("c.name = %s")
            params.append(category)
        where_clause = " AND ".join(conditions)
        
        expense_query = f"""
            SELECT e.expense_id, c.name AS category, e.date, e.amount, e.payment_method, e.description
            FROM expense e
            JOIN categories c ON e.category_id = c.category_id
            WHERE {where_clause}
            ORDER BY e.date DESC, e.expense_id DESC
        """
        
        with connection.cursor() as cursor:
            cursor.execute(expense_query, params)
            rows = cursor.fetchall()
        
        results = []
        for row in rows:
            expense_id, category_name, dt, amount, payment_method, description = row
            # Ensure dt is a datetime object.
            if not isinstance(dt, datetime):
                try:
                    dt = datetime.strptime(str(dt), "%Y-%m-%d %H:%M:%S")
                except Exception:
                    dt = datetime.now()
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M:%S")
            results.append({
                'expense_id': expense_id,
                'category': category_name,
                'date': date_str,
                'time': time_str,
                'amount': amount,
                'payment_method': payment_method,
                'description': description,
            })
        
        return Response(results, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
def delete_expense(request, expense_id):
    """
    Deletes the specified expense for the authenticated user.
    """
    token = request.headers.get('Authorization') or request.GET.get('token')
    if not token:
        return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
    if token.startswith("Bearer "):
        token = token[7:]
    
    try:
        # Validate token.
        user_token = execute_query("SELECT user_id FROM user_token WHERE token = %s", [token], fetch_one=True)
        if not user_token:
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
        user_id = user_token[0]
        
        # Delete expense only if it belongs to the authenticated user.
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM expense WHERE expense_id = %s AND user_id = %s", [expense_id, user_id])
            if cursor.rowcount == 0:
                return Response({'error': 'Expense not found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({'message': 'Expense deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_categories(request):
    """
    Retrieves a list of category names for a dropdown.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM categories ORDER BY name ASC")
            rows = cursor.fetchall()
        categories = [row[0] for row in rows]
        return Response(categories, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
