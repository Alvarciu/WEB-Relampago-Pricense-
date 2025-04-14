from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings


### --- MODELO DE USUARIO --- ###

#  Esta clase maneja la creación de usuarios. 
# Es como un asistente para que el sistema pueda crear usuarios correctamente. Tiene dos métodos importantes:
class UsuarioManager(BaseUserManager):
    

    #Este método crea un usuario normal. Primero valida que el email sea válido, 
    # luego normaliza el email (para que no importe si el usuario lo escribe en mayúsculas o minúsculas) 
    # y luego guarda la contraseña de forma segura.
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        usuario = self.model(email=email, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    # Este método crea un "superusuario", es decir, un usuario con privilegios de administrador, 
    # que puede acceder a la sección de administración del sitio. 
    # Lo que hace es llamar a create_user pero asegurándose de que el superusuario tenga permisos
    #  de administrador (como "is_staff" y "is_superuser").
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

#Esta clase define cómo se estructura el modelo de datos para los usuarios de tu sistema
class Usuario(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(unique=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_gestor = models.BooleanField(default=False)

    #le decimos que utilice email en lugar de username.
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'apellidos']

    #estás diciendo que quieres usar ese gestor personalizado para todas las operaciones de acceso a los usuarios, 
    # como crear, obtener o modificar usuarios. 
    # En lugar de usar el gestor predeterminado de Django, ahora el modelo Usuario usa tu propio UsuarioManager.
    objects = UsuarioManager()

    #Este método devuelve el email del usuario como su representación en texto. 
    # Entonces, si tienes un objeto usuario, y haces algo como print(usuario), lo que se imprimirá será el email del usuario.
    def __str__(self):
        return self.email

    def delete(self, *args, **kwargs):
        self.mensajes.all().delete()
        super().delete(*args, **kwargs)


### --- MODELO DE PRODUCTO --- ###

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


### --- MODELO DE PEDIDO --- ###

#Este modelo representa un pedido realizado por un usuario. 
# Es como el "contenedor" donde se guarda toda la información sobre la compra:
class Pedido(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pedidos')
    fecha = models.DateTimeField(auto_now_add=True)
    pagado = models.BooleanField(default=False)

    #lo que significa que se comporta como un atributo normal, pero en realidad es un cálculo que se realiza cuando lo accedes.
    @property
    def total(self):
        return sum(linea.producto.precio for linea in self.lineas.all())

    def __str__(self):
        return f"Pedido {self.id} de {self.usuario.email}"


# Cada "línea de pedido" representa un producto que el usuario ha comprado en ese pedido. 
# Si alguien compra varias camisetas, habrá varias líneas de pedido, una para cada camiseta.
class LineaPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='lineas')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    talla = models.CharField(max_length=10)
    nombre_dorsal = models.CharField(max_length=100, blank=True, null=True)
    numero_dorsal = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.producto.nombre} x1"


### --- CONFIGURACIÓN GLOBAL --- ###

#Este modelo guarda la configuración general del sistema, 
# en este caso, simplemente guarda si los pedidos están abiertos o no.
class Configuracion(models.Model):
    pedidos_abiertos = models.BooleanField(default=True)

    def __str__(self):
        return "Configuración general"

    class Meta:
        verbose_name = "Configuración"
        verbose_name_plural = "Configuración"


def get_configuracion():
    config, created = Configuracion.objects.get_or_create(id=1)
    return config
