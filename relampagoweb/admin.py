from django.contrib import admin
from . import models
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Usuario

# Register your models here.
# admin.site.register(models.Producto)

class UsuarioAdmin(BaseUserAdmin):
    model = Usuario
    list_display = ('email', 'name', 'apellidos', 'telefono', 'is_staff', 'is_superuser', 'mostrar_es_gestor')
    list_filter = ('is_staff', 'is_superuser')
    search_fields = ('email', 'name', 'apellidos')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Información personal'), {'fields': ('name', 'apellidos', 'telefono')}),
        (_('Permisos'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
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


    def mostrar_es_gestor(self, obj):
        return obj.es_gestor
    mostrar_es_gestor.boolean = True  # ✅ Muestra check verde o cruz
    mostrar_es_gestor.short_description = "Es gestor"

admin.site.register(Usuario, UsuarioAdmin)