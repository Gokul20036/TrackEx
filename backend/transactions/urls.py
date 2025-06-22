from django.urls import path
from .views import add_transaction, get_recent_transaction

urlpatterns = [
    path('add/', add_transaction, name='add_transaction'),
    path('latest/', get_recent_transaction, name='get_recent_transaction'),
]
