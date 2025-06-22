from django.http import JsonResponse
from django.db import connection
import bcrypt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import SignupSerializer, LoginSerializer
from rest_framework.authtoken.models import Token
import uuid
from datetime import datetime

def execute_query(query, params=None, fetch_one=False):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        if fetch_one:
            return cursor.fetchone()
        return cursor.fetchall()



@api_view(['POST'])
def signup(request):
    if request.method == 'POST':
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            re_password = serializer.validated_data['re_password']
            if password != re_password:
                return Response({'error': 'Passwords do not match'}, status=400)

            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            existing_user_query = "SELECT * FROM user WHERE username = %s OR email = %s"
            existing_user = execute_query(existing_user_query, [username, email], fetch_one=True)
            if existing_user:
                return Response({'error': 'Username or email already exists'}, status=400)

            try:
                # Insert new user into the database
                query = "INSERT INTO user (username, email, password) VALUES (%s, %s, %s)"
                execute_query(query, [username, email, hashed_password])
                return Response({'message': 'User registered successfully'}, status=201)
            except Exception as e:
                return Response({'error': str(e)}, status=400)

        return Response(serializer.errors, status=400)


# Login View
@api_view(['POST'])
def login(request):
    if request.method == 'POST':
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            # Retrieve user details
            query = "SELECT user_id, password FROM user WHERE username = %s"
            result = execute_query(query, [username], fetch_one=True)

            if result:
                user_id, stored_password = result
                if bcrypt.checkpw(password.encode(), stored_password.encode()):
                    # Check if a token already exists for the user
                    token_query = "SELECT token FROM user_token WHERE user_id = %s"
                    token_result = execute_query(token_query, [user_id], fetch_one=True)

                    if token_result:
                        # Return existing token
                        token = token_result[0]
                    else:
                        # Generate and save a new token
                        token = uuid.uuid4().hex
                        insert_token_query = "INSERT INTO user_token (user_id, token) VALUES (%s, %s)"
                        execute_query(insert_token_query, [user_id, token])

                    return Response({'message': 'Login successful', 'token': token}, status=200)

                return Response({'error': 'Invalid credentials'}, status=401)

            return Response({'error': 'User not found'}, status=404)

        return Response(serializer.errors, status=400)
    
@api_view(['GET', 'POST'])
def logout(request):
    # Get token from either Authorization header or query parameters
    token = request.headers.get('Authorization') or request.GET.get('token')
    if not token:
        return Response({'error': 'Token is required in the Authorization header or as a query parameter'}, status=400)
    if token.startswith("Bearer "):
        token = token[7:]
    try:
        # Delete the token row from the database
        query = "DELETE FROM user_token WHERE token = %s"
        execute_query(query, [token])
        return Response({'message': 'Logged out successfully'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

