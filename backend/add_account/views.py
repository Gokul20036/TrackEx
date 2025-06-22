from datetime import datetime
from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import AddAccountDetailsSerializer, VerifyPinSerializer

# Utility function to execute SQL queries.
def execute_query(query, params=None, fetch_one=False):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        return cursor.fetchone() if fetch_one else cursor.fetchall()

# Extracts and validates the user token.
def get_user_id_from_request(request):
    token = request.headers.get('Authorization') or request.GET.get('token')
    if not token:
        return None
    if token.startswith("Bearer "):
        token = token[7:]
    query = "SELECT user_id FROM user_token WHERE token = %s"
    user_token = execute_query(query, [token], fetch_one=True)
    return user_token[0] if user_token else None

# Masks all but the last 4 digits of the account number.
def mask_account_number(account_number: str) -> str:
    account_number = str(account_number)  # Ensure it's a string
    return account_number if len(account_number) <= 4 else "x" * (len(account_number) - 4) + account_number[-4:]

@api_view(['POST'])
def add_account_details(request):
    """
    POST endpoint to verify bank account details, including the unique code,
    link them to the user, and store the provided 4-digit PIN.
    """
    user_id = get_user_id_from_request(request)
    if user_id is None:
        return Response({'error': 'Token is required or is invalid'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = AddAccountDetailsSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data

        # Verify bank account details along with the unique_code.
        query = """
            SELECT bank_acc_id, balance
            FROM bank_accounts
            WHERE account_number = %s
              AND account_holder_name = %s
              AND bank_name = %s
              AND branch_name = %s
              AND ifsc_code = %s
              AND unique_code = %s
        """
        result = execute_query(query, [
            data.get('account_number'),
            data.get('account_holder_name'),
            data.get('bank_name'),
            data.get('branch_name'),
            data.get('ifsc_code'),
            data.get('unique_code')
        ], fetch_one=True)

        if not result:
            return Response(
                {"detail": "Bank account details do not match any record."},
                status=status.HTTP_400_BAD_REQUEST
            )

        bank_acc_id = result[0]
        pin_no = data.get('pin_no')  # New field for PIN number

        # Check if the user already has account details.
        existing = execute_query("SELECT app_acc_id FROM app_accounts WHERE user_id = %s", [user_id], fetch_one=True)
        if existing:
            # Update existing record with bank_acc_id and pin_no.
            execute_query(
                "UPDATE app_accounts SET bank_acc_id = %s, pin_no = %s WHERE user_id = %s",
                [bank_acc_id, pin_no, user_id]
            )
        else:
            # Insert a new record including pin_no.
            execute_query(
                "INSERT INTO app_accounts (user_id, bank_acc_id, pin_no) VALUES (%s, %s, %s)",
                [user_id, bank_acc_id, pin_no]
            )

        return Response({"detail": "Account details successfully added/updated."}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_account_details(request):
    """
    GET endpoint to retrieve and return masked account details for the user.
    """
    user_id = get_user_id_from_request(request)
    if user_id is None:
        return Response({'error': 'Token is required or is invalid'}, status=status.HTTP_400_BAD_REQUEST)

    query = """
        SELECT b.account_number, b.balance
        FROM bank_accounts b
        JOIN app_accounts a ON b.bank_acc_id = a.bank_acc_id
        WHERE a.user_id = %s
    """
    row = execute_query(query, [user_id], fetch_one=True)
    if row:
        account_number, balance = row
        masked_account_number = mask_account_number(account_number)
        return Response(
            {"account_number": masked_account_number, "balance": str(balance)},
            status=status.HTTP_200_OK
        )
    return Response({"detail": "No account details found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_monthly_expense(request):
    """
    GET endpoint to retrieve the total monthly expense for the user.
    """
    user_id = get_user_id_from_request(request)
    if user_id is None:
        return Response({'error': 'Token is required or is invalid'}, status=status.HTTP_400_BAD_REQUEST)

    now = datetime.now()
    current_month = now.month
    current_year = now.year

    query = """
        SELECT COALESCE(SUM(amount), 0) AS total_spent
        FROM expense
        WHERE user_id = %s
          AND MONTH(date) = %s
          AND YEAR(date) = %s
    """

    row = execute_query(query, [user_id, current_month, current_year], fetch_one=True)
    total_spent = row[0] if row else 0

    return Response({"total_spent": total_spent})

@api_view(['POST'])
def verify_pin(request):
    """
    POST endpoint to verify the 4-digit PIN and return the actual account balance if correct.
    This is intended to be used when the user taps the "i" button in your Flutter app.
    """
    user_id = get_user_id_from_request(request)
    if user_id is None:
        return Response({'error': 'Token is required or is invalid'}, status=status.HTTP_400_BAD_REQUEST)

    # Validate the incoming PIN using the VerifyPinSerializer.
    serializer = VerifyPinSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    pin = serializer.validated_data.get('pin')

    # Retrieve the stored PIN for the user.
    query = "SELECT pin_no FROM app_accounts WHERE user_id = %s"
    row = execute_query(query, [user_id], fetch_one=True)
    if row:
        stored_pin = row[0]
        # Compare provided PIN with stored PIN (as strings).
        if str(stored_pin) == str(pin):
            # PIN is correct; now fetch the actual balance.
            query = """
                SELECT b.balance
                FROM bank_accounts b
                JOIN app_accounts a ON b.bank_acc_id = a.bank_acc_id
                WHERE a.user_id = %s
            """
            account_row = execute_query(query, [user_id], fetch_one=True)
            if account_row:
                balance = account_row[0]
                return Response({"balance": str(balance)}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Account not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "Incorrect PIN"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"detail": "No account details found."}, status=status.HTTP_404_NOT_FOUND)
