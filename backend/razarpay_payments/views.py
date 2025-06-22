import json
import razorpay
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from .models import Payment
from .serializers import CreateOrderSerializer, PaymentSerializer

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@api_view(['POST'])
def create_order(request):
    serializer = CreateOrderSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    amount = int(serializer.validated_data['amount'])  # Amount should be in paise
    category = serializer.validated_data.get('category', 'Other')
    upi_id = serializer.validated_data.get('upi_id', '')
    mobile_number = serializer.validated_data.get('mobile_number', '')
    
    try:
        # Create order in Razorpay
        order_data = {
            'amount': amount,
            'currency': 'INR',
            'receipt': f'receipt_{amount}_{category}',
            'payment_capture': 1  # Auto-capture
        }
        order = client.order.create(data=order_data)
        
        # Save order to database
        payment = Payment(
            order_id=order['id'],
            amount=amount/100,  # Convert back to rupees for DB storage
            category=category,
            upi_id=upi_id,
            mobile_number=mobile_number
        )
        payment.save()
        
        # Add UPI specific details if provided
        response_data = {
            'order_id': order['id'],
            'amount': amount,
            'key_id': settings.RAZORPAY_KEY_ID,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def verify_payment(request):
    try:
        # Extract payment response data
        payment_id = request.data.get('payment_id')
        order_id = request.data.get('order_id')
        signature = request.data.get('signature')
        payment_method = request.data.get('payment_method', '')
        
        # Verify signature
        params_dict = {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': order_id,
            'razorpay_signature': signature
        }
        
        # Verify the payment signature
        client.utility.verify_payment_signature(params_dict)
        
        # Update payment in database
        try:
            payment = Payment.objects.get(order_id=order_id)
            payment.payment_id = payment_id
            payment.signature = signature
            payment.status = 'successful'
            payment.payment_method = payment_method
            payment.save()
            
            serializer = PaymentSerializer(payment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        # Update payment as failed if there was an exception
        if order_id:
            try:
                payment = Payment.objects.get(order_id=order_id)
                payment.status = 'failed'
                payment.save()
            except Payment.DoesNotExist:
                pass
        
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def payment_history(request):
    payments = Payment.objects.all().order_by('-created_at')
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)