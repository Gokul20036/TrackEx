"""
URL configuration for project_name project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
#from django.urls import path
from django.urls import path, include
from django.http import HttpResponse
from rest_framework.authtoken.views import obtain_auth_token


# Define a simple view for the root URL


urlpatterns = [
      # Root URL pattern pointing to the home view
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api-token-auth/', obtain_auth_token),
    path('api/transactions/', include('transactions.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/stock_prediction/', include('stock_prediction.urls')),
    path('api/categories/', include('categories.urls')),
    path('api/', include('transaction_history.urls')),
    path('api/', include('transaction_history.urls')),
    path('api/payment/', include('payment.urls')),
    path('', include('add_account.urls')), 
    path('api/categorize/', include('categorize.urls')),
    path('api/profilee/', include('profilee.urls')),
    path('api/', include('tax_api.urls')),
    path('api/', include('razarpay_payments.urls')),
]
