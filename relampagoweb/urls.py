from django.urls import path
from .views import registro_view, login_view, logout_view
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .views import (
    registro_view,
    login_view,
    logout_view,
    tienda_view,
    detalle_producto_view,
    añadir_al_carrito_view,
    carrito_view,
    eliminar_del_carrito_view
)

urlpatterns = [
    path('registro/', registro_view, name='registro'),
     path('accounts/login/', login_view , name='login'),
    path('logout/', logout_view, name='logout'),
    path('', login_required(lambda request: render(request, 'inicio.html')), name='inicio'),
    path('tienda/', tienda_view, name='tienda'),
    path('producto/<int:producto_id>/', detalle_producto_view, name='detalle_producto'),
    path('añadir-al-carrito/<int:producto_id>/', añadir_al_carrito_view, name='añadir_al_carrito'),
    path('carrito/', carrito_view, name='carrito'),
    path('carrito/eliminar/<int:item_index>/', eliminar_del_carrito_view, name='eliminar_del_carrito'),

]
