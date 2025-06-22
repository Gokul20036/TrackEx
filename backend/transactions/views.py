from datetime import datetime
from django.db import connection
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
import uuid

# Function to execute database queries
def execute_query(query, params=None, fetch_one=False):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        if fetch_one:
            return cursor.fetchone()
        return cursor.fetchall()

# -------------------------------------------
# View for adding a transaction (with description)
# -------------------------------------------
@api_view(['POST'])
def add_transaction(request):
    # Extract the token from the Authorization header or query parameter.
    token = request.headers.get('Authorization') or request.GET.get('token')
    if not token:
        return Response(
            {'error': 'Token is required in the Authorization header or as a query parameter'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if token.startswith("Bearer "):
        token = token[7:]  # Remove "Bearer " prefix

    try:
        # Find the user associated with the token.
        query = "SELECT user_id FROM user_token WHERE token = %s"
        user_token = execute_query(query, [token], fetch_one=True)
        if not user_token:
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
        user_id = user_token[0]

        # Extract transaction details from the request data.
        # Now expected: 'category_name', 'category_description', 'amount', 'date', and 'payment_method'
        category_name = request.data.get('category_name')
        category_description = request.data.get('category_description')
        amount = request.data.get('amount')
        date_str = request.data.get('date')
        payment_method = request.data.get('payment_method')

        # Validate that all fields are provided.
        if not category_name or not category_description or not amount or not date_str or not payment_method:
            return Response({'error': 'Please fill all fields'}, status=status.HTTP_400_BAD_REQUEST)

        # Combine the user-provided date with the current time.
        try:
            user_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            current_time = datetime.now().time()
            dt = datetime.combine(user_date, current_time)
        except Exception as e:
            dt = datetime.now()
        dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")

        # Get the category_id by category_name.
        category_query = "SELECT category_id FROM categories WHERE name = %s"
        category = execute_query(category_query, [category_name], fetch_one=True)
        if not category:
            return Response({'error': 'Invalid category name'}, status=status.HTTP_400_BAD_REQUEST)
        category_id = category[0]

        # Insert the expense record into the expense table including the new description.
        insert_expense_query = """
            INSERT INTO expense (user_id, category_id, amount, date, payment_method, description)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        execute_query(insert_expense_query, [user_id, category_id, amount, dt_str, payment_method, category_description])

        return Response({"message": "Transaction added successfully"}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --------------------------------------------------------------
# New Function: Get the Last 3 Transactions for the current user
# Returns category, description, amount, date, and time (separately)
# --------------------------------------------------------------
@api_view(['GET'])
def get_recent_transaction(request):
    # Extract the token from the Authorization header or query parameter.
    token = request.headers.get('Authorization') or request.GET.get('token')
    if not token:
        return Response(
            {'error': 'Token is required in the Authorization header or as a query parameter'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if token.startswith("Bearer "):
        token = token[7:]  # Remove "Bearer " prefix
  
    try:
        # Get the user_id associated with the token.
        query = "SELECT user_id FROM user_token WHERE token = %s"
        user_token = execute_query(query, [token], fetch_one=True)
        if not user_token:
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
        user_id = user_token[0]

        # Fetch the last 3 transactions for this user using a JOIN to get the category name.
        latest_query = """
            SELECT c.name, e.description, e.amount, e.date 
            FROM expense e
            JOIN categories c ON e.category_id = c.category_id
            WHERE e.user_id = %s
            ORDER BY e.date DESC, e.expense_id DESC
            LIMIT 3
        """
        transactions = execute_query(latest_query, [user_id])
        if not transactions:
            return Response({'error': 'No transactions found for this user'}, status=status.HTTP_404_NOT_FOUND)

        results = []
        for row in transactions:
            cat_name, description, amount, dt = row
            # Ensure dt is a datetime object.
            if not isinstance(dt, datetime):
                try:
                    dt = datetime.strptime(str(dt), "%Y-%m-%d %H:%M:%S")
                except Exception:
                    dt = datetime.now()  # Fallback if needed
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M:%S")
            results.append({
                'category': cat_name,
                'description': description,
                'amount': amount,
                'date': date_str,
                'time': time_str,
            })

        return Response(results, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
