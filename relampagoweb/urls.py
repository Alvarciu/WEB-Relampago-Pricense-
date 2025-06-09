from django.urls import path
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .views import *
from django.contrib.auth import views as auth_views
from relampagoweb.views import CustomPasswordResetView
from django.urls import reverse

urlpatterns = [
    # Inicio y autenticación
    path('', login_required(inicio_view), name='inicio'),
    path('registro/', registro_view, name='registro'),
    path('accounts/login/', login_view , name='login'),
    path('logout/', logout_view, name='logout'),

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
    path('pedido/<str:pedido_id>/cambiar_estado/', cambiar_estado_pedido, name='cambiar_estado_pedido'),

    # Administración
    path('exportar-pedidos/', exportar_pedidos_excel , name='exportar_pedidos_excel'),
    path('panel/pedidos/', lista_pedidos_view, name='lista_pedidos'),
    path('panel/pedidos/toggle/', alternar_pedidos_view, name='alternar_pedidos'),
    path('panel/pedidos/<str:pedido_id>/', detalle_pedido_admin_view, name='detalle_pedido_admin'),
    path('panel/', panel_pedidos_view, name='panel_pedidos'),

    # Recuperación de contraseña
    path(
        'password_reset/',
        CustomPasswordResetView.as_view(
            template_name='contraseña/password_reset_form.html',
            email_template_name='emails/password_reset.html',
            subject_template_name='emails/password_reset_subject.txt',
            success_url='/password_reset/done/'
        ),
        name='password_reset'
    ),
    path(
        'password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='contraseña/password_reset_done.html'),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='contraseña/password_reset_confirm.html'),
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(template_name='contraseña/password_reset_complete.html'),
        name='password_reset_complete'
    ),
]
