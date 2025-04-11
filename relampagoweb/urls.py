from django.urls import path
from .views import registro_view, login_view, logout_view
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .views import *

urlpatterns = [
    path('', login_required(inicio_view), name='inicio'),
    path('registro/', registro_view, name='registro'),
     path('accounts/login/', login_view , name='login'),
    path('logout/', logout_view, name='logout'),
    path('', login_required(lambda request: render(request, 'inicio.html')), name='inicio'),
    path('tienda/', tienda_view, name='tienda'),
    path('producto/<int:producto_id>/', detalle_producto_view, name='detalle_producto'),
    path('añadir-al-carrito/<int:producto_id>/', añadir_al_carrito_view, name='añadir_al_carrito'),
    path('carrito/', carrito_view, name='carrito'),
    path('carrito/eliminar/<int:item_index>/', eliminar_del_carrito_view, name='eliminar_del_carrito'),
    path('carrito/editar/<int:item_index>/', editar_item_carrito_view, name='editar_item_carrito'),
    path('carrito/vaciar/', vaciar_carrito_view, name='vaciar_carrito'),
    path('exportar-pedidos/', exportar_pedidos_excel , name='exportar_pedidos_excel'),
    path('panel/pedidos/', lista_pedidos_view, name='lista_pedidos'),
    path('panel/pedidos/<int:pedido_id>/', detalle_pedido_admin_view, name='detalle_pedido_admin'),
    path('panel/pedidos/toggle/', alternar_pedidos_view, name='alternar_pedidos'),
]

