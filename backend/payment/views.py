from django.db import connection, transaction
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import pytz

# Utility function to execute raw SQL queries.
def execute_query(query, params=None, fetch_one=False):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        return cursor.fetchone() if fetch_one else cursor.fetchall()

# Extract the user_id from the request token.
def get_user_id_from_request(request):
    token = request.headers.get('Authorization') or request.GET.get('token')
    if not token:
        return None
    if token.startswith("Bearer "):
        token = token[7:]
    query = "SELECT user_id FROM user_token WHERE token = %s"
    user_token = execute_query(query, [token], fetch_one=True)
    return user_token[0] if user_token else None

@api_view(['POST'])
def process_payment(request):
    """
    POST endpoint to process a payment transaction.
    
    Expected JSON payload:
    {
      "account_number": "recipient account number",
      "recipient_name": "recipient account holder name",
      "ifsc_code": "recipient IFSC code",
      "amount": <transaction amount>,
      "pin_no": "4-digit PIN"
    }
    """
    user_id = get_user_id_from_request(request)
    if user_id is None:
        return Response({'error': 'Token is required or is invalid.'},
                        status=status.HTTP_400_BAD_REQUEST)
    
    # Verify that the sender has added bank details, including the PIN.
    sender_app = execute_query(
        "SELECT bank_acc_id, pin_no FROM app_accounts WHERE user_id = %s",
        [user_id],
        fetch_one=True
    )
    if not sender_app or not sender_app[0]:
        return Response({'error': 'Please add bank details before making a payment.'},
                        status=status.HTTP_400_BAD_REQUEST)
    
    # Retrieve the stored PIN from sender's bank details.
    stored_pin = sender_app[1]
    
    # Get and validate the payment details.
    data = request.data
    recipient_account_number = data.get('account_number')
    recipient_name = data.get('recipient_name')
    recipient_ifsc = data.get('ifsc_code')
    amount = data.get('amount')
    provided_pin = data.get('pin_no')
    
    # Check if PIN is provided.
    if not provided_pin:
        return Response({'error': 'PIN is required.'},
                        status=status.HTTP_400_BAD_REQUEST)
    
    # Check if the provided PIN matches the stored PIN.
    if stored_pin is None or stored_pin != provided_pin:
        return Response({'error': 'Wrong PIN.'},
                        status=status.HTTP_400_BAD_REQUEST)
    
    if not (recipient_account_number and recipient_name and recipient_ifsc and amount):
        return Response({'error': 'All fields (account_number, recipient_name, ifsc_code, amount) are required.'},
                        status=status.HTTP_400_BAD_REQUEST)
    
    try:
        amount = float(amount)
        if amount <= 0:
            return Response({'error': 'Amount must be positive.'},
                            status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({'error': 'Invalid amount.'},
                        status=status.HTTP_400_BAD_REQUEST)
    
    # Find the recipient’s bank account details.
    query = """
        SELECT bank_acc_id, balance
        FROM bank_accounts
        WHERE account_number = %s
          AND account_holder_name = %s
          AND ifsc_code = %s
    """
    recipient_acc = execute_query(query,
                                  [recipient_account_number, recipient_name, recipient_ifsc],
                                  fetch_one=True)
    if not recipient_acc:
        return Response({'error': 'No account found for the entered recipient details.'},
                        status=status.HTTP_400_BAD_REQUEST)
    
    recipient_bank_acc_id = recipient_acc[0]
    
    # Check if sender has sufficient funds.
    sender_query = "SELECT balance FROM bank_accounts WHERE bank_acc_id = %s"
    sender_acc = execute_query(sender_query, [sender_app[0]], fetch_one=True)
    if not sender_acc:
        return Response({'error': 'Sender account details not found.'},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        sender_balance = float(sender_acc[0])
    except (ValueError, TypeError):
        return Response({'error': 'Invalid sender balance.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    if sender_balance < amount:
        return Response({'error': 'Insufficient balance.'},
                        status=status.HTTP_400_BAD_REQUEST)
    
    # Perform the transaction in an atomic block.
    try:
        with transaction.atomic():
            # Deduct the amount from sender's account.
            update_sender_query = "UPDATE bank_accounts SET balance = balance - %s WHERE bank_acc_id = %s"
            execute_query(update_sender_query, [amount, sender_app[0]])
            
            # Add the amount to recipient's account.
            update_recipient_query = "UPDATE bank_accounts SET balance = balance + %s WHERE bank_acc_id = %s"
            execute_query(update_recipient_query, [amount, recipient_bank_acc_id])
            
            # Dynamically fetch the category_id for "Account Transfer".
            cat_query = "SELECT category_id FROM categories WHERE name = %s"
            cat = execute_query(cat_query, ["ACCOUNT TRANSFER"], fetch_one=True)
            if not cat:
                raise Exception("Category 'Account Transfer' not found.")
            category_id = cat[0]
            
            # Convert the current time to IST.
            current_time = timezone.now().astimezone(pytz.timezone("Asia/Kolkata"))
            
            # Record this transaction in the expense table with description.
            insert_expense_query = """
                INSERT INTO expense (user_id, category_id, amount, date, payment_method, description)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            description = f"Paid to {recipient_name}"
            execute_query(insert_expense_query, [user_id, category_id, amount, current_time, 'Account Transfer', description])
            
        return Response({'detail': 'Payment successful.'},
                        status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'Transaction failed. ' + str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
