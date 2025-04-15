from django.contrib import admin
from . import models
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import *
from django.contrib import admin
from .models import Producto

# Register your models here.
admin.site.register(Producto)

class UsuarioAdmin(BaseUserAdmin):
    model = Usuario
    list_display = ('email', 'name', 'apellidos', 'telefono', 'password', 'is_staff', 'is_superuser', 'mostrar_es_gestor')
    list_filter = ('is_staff', 'is_superuser')
    search_fields = ('email', 'name', 'apellidos')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Información personal'), {'fields': ('name', 'apellidos', 'telefono')}),
        (_('Permisos'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'es_gestor')}),
        (_('Fechas importantes'), {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'apellidos', 'telefono', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )

    def delete_model(self, request, obj):
        obj.mensajes.all().delete()
        super().delete_model(request, obj)

    # Funcion totalmente irrelevante:
    def mostrar_es_gestor(self, obj):
        return obj.es_gestor
    mostrar_es_gestor.boolean = True  # ✅ Muestra check verde o cruz
    mostrar_es_gestor.short_description = "Es gestor"

admin.site.register(Usuario, UsuarioAdmin)

class LineaPedidoInline(admin.TabularInline):
    model = LineaPedido
    extra = 0
    readonly_fields = ['producto', 'talla', 'nombre_dorsal', 'numero_dorsal']
    can_delete = False

class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'pagado', 'fecha', 'total']
    readonly_fields = ['mostrar_total', 'mostrar_serigrafiados']
    inlines = [LineaPedidoInline]

    def mostrar_total(self, obj):
        return f"{obj.total} €"
    mostrar_total.short_description = "Total del pedido"

    def mostrar_serigrafiados(self, obj):
        lineas = obj.lineas.all()
        serigrafiados = [linea for linea in lineas if linea.nombre_dorsal or linea.numero_dorsal]
        return "Sí" if serigrafiados else "No"
    mostrar_serigrafiados.short_description = "¿Serigrafiado?"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        pedido = Pedido.objects.get(pk=object_id)
        extra_context = extra_context or {}
        extra_context['title'] = f"Pedido {pedido.id} de {pedido.usuario.email}"
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

admin.site.register(Pedido, PedidoAdmin)
admin.site.register(LineaPedido)
