from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import connection

def execute_query(query, params=None, fetch_one=False):
    """
    Execute a raw SQL query.
    """
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        if fetch_one:
            return cursor.fetchone()
        return cursor.fetchall()

@api_view(['GET'])
def account_details(request):
    """
    Fetch account details (account number and balance) for the currently logged-in user.
    The current user is determined using your custom token system.
    """
    # Extract the token from the Authorization header or query parameter.
    token = request.headers.get('Authorization') or request.GET.get('token')
    if not token:
        return Response(
            {'error': 'Token is required in the Authorization header or as a query parameter'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Remove "Bearer " prefix if present.
    if token.startswith("Bearer "):
        token = token[7:]

    try:
        # Retrieve the user_id associated with the token.
        query = "SELECT user_id FROM user_token WHERE token = %s"
        user_token = execute_query(query, [token], fetch_one=True)
        if not user_token:
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
        user_id = user_token[0]

        # Use raw SQL to fetch account details by joining app_accounts and bank_accounts.
        account_query = """
            SELECT b.account_number, b.balance
            FROM app_accounts a
            JOIN bank_accounts b ON a.bank_acc_id = b.bank_acc_id
            WHERE a.user_id = %s
        """
        row = execute_query(account_query, [user_id], fetch_one=True)
        if not row:
            return Response({'detail': 'No account details found.'}, status=status.HTTP_404_NOT_FOUND)
        
        account_number, balance = row
        data = {
            'account_number': account_number,
            'balance': float(balance),
        }
        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
