from django.urls import path
from .views import delete_expense, get_categories, get_expenses

urlpatterns = [
    path('expenses/', get_expenses, name='get_expenses'),
     path('expenses/<int:expense_id>/', delete_expense, name='delete_expense'),
    path('categories/', get_categories, name='get_categories'),
]
