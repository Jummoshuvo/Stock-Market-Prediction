from django.urls import path
from . import views

urlpatterns = [
    path('predict/', views.predict_stock, name='predict_stock'),
    path('stocks/', views.get_stock_list, name='get_stock_list'),
    path('contact/', views.contact_form, name='contact_form'),
    path('trading-data/', views.trading_data, name='trading_data'),
]

