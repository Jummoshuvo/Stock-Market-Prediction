"""
URL configuration for stockpredictor project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from predictor.views import news_detail, signup_view, login_view, logout_view, trading_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('predictor.urls')),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('trading/', trading_view, name='trading'),
    path('news/<str:slug>/', news_detail, name='news_detail'),
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]

