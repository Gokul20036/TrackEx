# urls.py
from django.urls import path

from .views import add_account_details,get_account_details, get_monthly_expense, verify_pin

urlpatterns = [
    path('api/add_account_details/', add_account_details, name='add_account_details'),
    path('api/account_details/',get_account_details, name='account_details'),
    path('api/monthly_expense/',get_monthly_expense,name='monthly_expense'),
    path('api/verify_pin/', verify_pin, name='verify_pin'),
]
