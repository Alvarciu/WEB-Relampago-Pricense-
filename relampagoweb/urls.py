from django.urls import path
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .views import *
from django.contrib.auth import views as auth_views
from django.urls import reverse
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Inicio y autenticación
    path('', inicio_view, name='inicio'),
    path('registro/', registro_view, name='registro'),
    path('accounts/login/', login_view , name='login'),
    path('logout/', logout_view, name='logout'),
    path('verificar-email/', verificar_email, name='verificar_email'),  # <-- esta línea


    # Tienda
    path('tienda/', tienda_view, name='tienda'),
    path('producto/<int:producto_id>/', detalle_producto_view, name='detalle_producto'),
    path('añadir-al-carrito/<int:producto_id>/', añadir_al_carrito_view, name='añadir_al_carrito'),

    # Carrito
    path('carrito/', carrito_view, name='carrito'),
    path('carrito/eliminar/<int:item_index>/', eliminar_del_carrito_view, name='eliminar_del_carrito'),
    path('carrito/editar/<int:item_index>/', editar_item_carrito_view, name='editar_item_carrito'),
    path('carrito/vaciar/', vaciar_carrito_view, name='vaciar_carrito'),

    # Pedidos
    path('resumen-pedido/', resumen_pedido_view, name='resumen_pedido'),
    path('confirmar-pedido/', confirmar_pedido_view, name='confirmar_pedido'),
    path('pago-simulado/', pago_simulado_view, name='pago_simulado'),
    path('mis-pedidos/', mis_pedidos_view, name='mis_pedidos'),
    path('mis-pedidos/<str:pedido_id>/', detalle_mi_pedido_view, name='detalle_mi_pedido'),
    path('pedido/<str:pedido_id>/cambiar_estado/', cambiar_estado_pedido, name='cambiar_estado_pedido'),

    # Administración
    path('exportar-pedidos/', exportar_pedidos_excel , name='exportar_pedidos'),
    path('panel/pedidos/', lista_pedidos_view, name='lista_pedidos'),
    path('panel/pedidos/toggle/', alternar_pedidos_view, name='alternar_pedidos'),
    path('panel/pedidos/<str:pedido_id>/', detalle_pedido_admin_view, name='detalle_pedido_admin'),

    path("solicitar-reset-password/", solicitar_reset_password, name="solicitar-reset-password"),
    path("reset-password/<str:token>/", resetear_password, name="reset-password"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



