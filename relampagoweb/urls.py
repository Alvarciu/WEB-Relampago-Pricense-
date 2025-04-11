from django.urls import path
from .views import registro_view, login_view, logout_view
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

urlpatterns = [
    path('registro/', registro_view, name='registro'),
     path('accounts/login/', login_view , name='login'),
    path('logout/', logout_view, name='logout'),
    path('', login_required(lambda request: render(request, 'inicio.html')), name='inicio'),
]
