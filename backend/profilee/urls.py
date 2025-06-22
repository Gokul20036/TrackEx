from django.urls import path
from .views import change_password, change_pin, get_account_holder_name, get_account_number

urlpatterns = [
    path('account-holder/', get_account_holder_name, name='account-holder'),
    path('account-number/', get_account_number, name='account-number'),
    path('change-password/', change_password, name='change-password'),
    path('change-pin/', change_pin, name='change-pin'),
]
