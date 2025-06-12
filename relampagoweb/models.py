from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
import shortuuid
from decimal import Decimal

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

    @property
    def es_gestor(self):
        return self.groups.filter(name="Gestores").exists()


### --- MODELO DE PRODUCTO --- ###

class Producto(models.Model):
    TIPO_PRODUCTO = (
        ('Camiseta', 'Camiseta'),
        ('Equipación', 'Equipación'),
        ('Sudadera', 'Sudadera'),
    )
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_PRODUCTO)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='productos/')
    precio = models.DecimalField(max_digits=6, decimal_places=2)    
    
    precio_camiseta_sola = models.DecimalField(
        max_digits=6, decimal_places=2,
        null=True, blank=True,
        help_text="Coste unitario de la camiseta suelta (si procede)"
    )

    precio_camiseta_descuento = models.DecimalField(
        max_digits=6, decimal_places=2,
        null=True, blank=True,
        help_text="Coste unitario de la camiseta suelta con descuento (si procede)"
    )

    coste_provedor= models.DecimalField(
        max_digits=6, decimal_places=2,
        null=False, blank=True,
        help_text="Precio que pagamos al proveedor por el producto, usar para equipaciones completas y sudaderas",
        default=Decimal('35.00')
    )

    coste_provedor_camiseta = models.DecimalField(
        max_digits=6, decimal_places=2,
        null=True, blank=True,
        help_text="Precio que pagamos al proveedor por la equipación solo camiseta",
        default=Decimal('22.00')
    )



    def __str__(self):
        return self.nombre


### --- MODELO DE PEDIDO --- ###

#Este modelo representa un pedido realizado por un usuario. 
# Es como el "contenedor" donde se guarda toda la información sobre la compra:
class Pedido(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pedidos')
    fecha = models.DateTimeField(auto_now_add=True)
    pagado = models.BooleanField(default=False)
    id = models.CharField(primary_key=True, max_length=22, default=shortuuid.uuid, editable=False)
    usar_descuento = models.BooleanField(default=False)

    from decimal import Decimal

    @property
    def total(self):
        PRECIO_CAMISETA_NORMAL   = Decimal('22.00')
        PRECIO_CAMISETA_DESC     = Decimal('20.00')

        total = Decimal('0.00')
        num_camisetas = 0

        # 1. Separar camisetas del resto de líneas
        for linea in self.lineas.all():
            if linea.compra_tipo == 'solo_camiseta':
                num_camisetas += 1
            else:
                total += linea.producto.precio

        # 2. Calcular subtotal de camisetas
        if num_camisetas:
            # Cuando hay descuento, solo cuentan los pares;
            # si no hay descuento, 'pares' será 0 y todas pagarán precio normal
            pares   = (num_camisetas // 2) if self.usar_descuento else 0
            sueltas = num_camisetas - (pares * 2)

            total += (pares * 2) * PRECIO_CAMISETA_DESC
            total += sueltas * PRECIO_CAMISETA_NORMAL

        return total

    def __str__(self):
        return f"Pedido {self.id} de {self.usuario.email}"


# Cada "línea de pedido" representa un producto que el usuario ha comprado en ese pedido. 
class LineaPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='lineas')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    talla = models.CharField(max_length=10)
    nombre_dorsal = models.CharField(max_length=100, blank=True, null=True)
    numero_dorsal = models.PositiveIntegerField(blank=True, null=True)
    compra_tipo = models.CharField(max_length=20, blank=True, null=True)  # <- AÑADIDO

    precio_unitario = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    costo_unitario  = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    @property
    def subtotal(self):
        return self.precio_unitario

    @property
    def subcosto(self):
        return self.costo_unitario

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


class Jugador(models.Model):
    nombre = models.CharField(max_length=100)
    posicion = models.CharField(max_length=50)
    foto = models.ImageField(upload_to='jugadores/')
    orden = models.PositiveIntegerField(default=0, help_text="Orden en la galería")

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"{self.nombre} ({self.posicion})"
