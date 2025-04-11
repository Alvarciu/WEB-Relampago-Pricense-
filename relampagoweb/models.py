### MODELOS DE USUARIO, PRODUCTO Y PEDIDO ###
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings


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

class Usuario(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(unique=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_gestor = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'apellidos']

    objects = UsuarioManager()

    def __str__(self):
        return self.email

    def delete(self, *args, **kwargs):
        self.mensajes.all().delete()
        super().delete(*args, **kwargs)

    @property
    def es_gestor(self):
        return self.groups.filter(name="Gestores").exists() ## esto hay que quitarlo, ya que no se usa en el admin

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

class Pedido(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pedidos')
    fecha = models.DateTimeField(auto_now_add=True)
    pagado = models.BooleanField(default=False)

    @property
    def total(self):
        return sum(linea.producto.precio for linea in self.lineas.all())

    def __str__(self):
        return f"Pedido {self.id} de {self.usuario.email}"

class LineaPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='lineas')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    talla = models.CharField(max_length=10)
    nombre_dorsal = models.CharField(max_length=100, blank=True, null=True)
    numero_dorsal = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.producto.nombre} x1"


class Configuracion(models.Model):
    pedidos_abiertos = models.BooleanField(default=True)

    def __str__(self):
        return "Configuración general"
    
    class Meta:
        verbose_name = "Configuración"
        verbose_name_plural = "Configuración"

# ✅ Función para obtener (o crear) la única configuración global
def get_configuracion():
    config, created = Configuracion.objects.get_or_create(id=1)
    return config

