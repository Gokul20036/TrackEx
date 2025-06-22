from django.utils.deprecation import MiddlewareMixin
from django.db import connection

# Function to execute database queries
def execute_query(query, params=None, fetch_one=False):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        if fetch_one:
            return cursor.fetchone()
        return cursor.fetchall()

class TokenMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Extract the token from the `Authorization` header
        token = request.headers.get('Authorization')
        if token:
            # Remove "Bearer " prefix if present
            if token.startswith("Bearer "):
                token = token[7:]
            
            # Validate the token by checking if it exists in the user_token table
            query = "SELECT user_id FROM user_token WHERE token = %s"
            result = execute_query(query, [token], fetch_one=True)
            if result:
                request.token = token  # Attach the token to the request
                request.user_id = result[0]  # Attach user_id to the request
            else:
                request.token = None
                request.user_id = None
        else:
            request.token = None
            request.user_id = None
