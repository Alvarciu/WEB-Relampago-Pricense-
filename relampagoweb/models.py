from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        usuario = self.model(email=email, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

# # El modelo Usuario corregido
# class Usuario(AbstractBaseUser, PermissionsMixin):
#     name = models.CharField(max_length=100)
#     apellidos = models.CharField(max_length=100)
#     telefono = models.CharField(max_length=20)
#     email = models.EmailField(unique=True)

#     is_active = models.BooleanField(default=True)
#     is_staff = models.BooleanField(default=False)

#     is_gestor=models.BooleanField(default=False)

#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['name', 'apellidos']

#     objects = UsuarioManager()

#     def __str__(self):
#         return self.email
    
#     def delete(self, *args, **kwargs):
#         self.mensajes.all().delete()
#         super().delete(*args, **kwargs)

#     @property
#     def es_gestor(self):
#         return self.groups.filter(name="Gestores").exists()

class Producto(models.Model):
    TIPO_PRODUCTO = (
        ('equipacion', 'Equipación'),
        ('sudadera', 'Sudadera'),
    )
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_PRODUCTO)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='productos/')
    precio = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.nombre