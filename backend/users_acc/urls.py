from django.urls import path
from .views import account_details

urlpatterns = [
    path('account_details/', account_details, name='account_details'),
]
