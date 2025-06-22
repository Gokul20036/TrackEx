# categorize/urls.py
from django.urls import path
from .views import get_budget_by_category, get_expense_for_category_current_month, insert_budget_by_category, update_budget_by_category

urlpatterns = [
    path('budget/', get_budget_by_category, name='get-budget-by-category'),
    path('budget/insert/', insert_budget_by_category, name='insert-budget-by-category'),
    path('expense/', get_expense_for_category_current_month, name='get-expense-for-category-current-month'),
    path('budget/update/', update_budget_by_category, name='update-budget-by-category'),
]
