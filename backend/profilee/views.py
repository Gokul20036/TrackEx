from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import bcrypt

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
def get_account_holder_name(request):
    """
    Retrieves the account holder name for the current logged in user.
    Expects a token (in the Authorization header or as a query parameter 'token').
    Uses a join between the app_accounts and bank_accounts tables.
    """
    user_id, error_response = get_user_id_from_token(request)
    if error_response:
        return error_response

    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT b.account_holder_name
                FROM bank_accounts b
                JOIN app_accounts a ON b.bank_acc_id = a.bank_acc_id
                WHERE a.user_id = %s
            """
            cursor.execute(sql, [user_id])
            result = cursor.fetchone()
        if result is not None:
            return Response({"account_holder_name": result[0]}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Account holder name not found for the current user."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_account_number(request):
    """
    Retrieves the account number for the current logged in user.
    Expects a token (in the Authorization header or as a query parameter 'token').
    Uses a join between the app_accounts and bank_accounts tables.
    """
    user_id, error_response = get_user_id_from_token(request)
    if error_response:
        return error_response

    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT b.account_number
                FROM bank_accounts b
                JOIN app_accounts a ON b.bank_acc_id = a.bank_acc_id
                WHERE a.user_id = %s
            """
            cursor.execute(sql, [user_id])
            result = cursor.fetchone()
        if result is not None:
            return Response({"account_number": result[0]}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Account number not found for the current user."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def change_password(request):
    """
    Changes the password for the current logged in user.
    Expects:
      - Token (in the Authorization header or as request data 'token')
      - old_password, new_password, confirm_password in request data.
    Verifies the old password using bcrypt and updates the user's password if valid.
    """
    user_id, error_response = get_user_id_from_token(request)
    if error_response:
        return error_response

    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')

    if not old_password or not new_password or not confirm_password:
        return Response({"error": "old_password, new_password and confirm_password are required."},
                        status=status.HTTP_400_BAD_REQUEST)
    
    if new_password != confirm_password:
        return Response({"error": "New passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Fetch the current hashed password from the user table.
        with connection.cursor() as cursor:
            cursor.execute("SELECT password FROM user WHERE user_id = %s", [user_id])
            result = cursor.fetchone()
        if result is None:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        stored_hashed_password = result[0]
        # Verify the old password using bcrypt.
        if not bcrypt.checkpw(old_password.encode(), stored_hashed_password.encode()):
            return Response({"error": "Old password is incorrect."}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Hash the new password
        new_hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        
        # Update the user's password.
        with connection.cursor() as cursor:
            update_query = "UPDATE user SET password = %s WHERE user_id = %s"
            cursor.execute(update_query, [new_hashed_password, user_id])
        
        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"error": f"An error occurred while changing the password: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def change_pin(request):
    """
    Changes the PIN for the current logged in user.
    Expects:
      - Token (in the Authorization header or as request data 'token')
      - old_pin, new_pin, confirm_pin in request data.
    Verifies the old PIN and updates it if the new PINs match.
    (PIN is stored in plain text.)
    """
    user_id, error_response = get_user_id_from_token(request)
    if error_response:
        return error_response

    old_pin = request.data.get('old_pin')
    new_pin = request.data.get('new_pin')
    confirm_pin = request.data.get('confirm_pin')

    if not old_pin or not new_pin or not confirm_pin:
        return Response({"error": "old_pin, new_pin and confirm_pin are required."},
                        status=status.HTTP_400_BAD_REQUEST)

    if new_pin != confirm_pin:
        return Response({"error": "New PINs do not match."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with connection.cursor() as cursor:
            # Fetch the current PIN from app_accounts.
            cursor.execute("SELECT pin_no FROM app_accounts WHERE user_id = %s", [user_id])
            result = cursor.fetchone()
        if result is None:
            return Response({"error": "User not found in app_accounts."}, status=status.HTTP_404_NOT_FOUND)
        
        stored_pin = result[0]
        # Check if the provided old PIN matches.
        if old_pin != stored_pin:
            return Response({"error": "Old PIN is incorrect."}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Update the PIN in app_accounts.
        with connection.cursor() as cursor:
            update_query = "UPDATE app_accounts SET pin_no = %s WHERE user_id = %s"
            cursor.execute(update_query, [new_pin, user_id])
        
        return Response({"message": "PIN changed successfully."}, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"error": f"An error occurred while changing the PIN: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
