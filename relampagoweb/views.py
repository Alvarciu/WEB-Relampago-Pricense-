# Librerías estándar de Python
import os
from decimal import Decimal
from email.mime.image import MIMEImage
import pandas as pd

# Django - Atajos y utilidades
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.http import Http404


# Django - Autenticación y permisos
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required

# Django - Formularios y modelos propios
from .forms import RegistroForm, LoginForm
from .models import Producto, Pedido, LineaPedido, Configuracion, get_configuracion

# Django - Correos
from django.core.mail import send_mail, send_mass_mail, EmailMultiAlternatives
from django.template.loader import render_to_string

# Django - Decoradores HTTP
from django.views.decorators.http import require_POST

from django.utils import translation

# Django - Recuperacion de contraseñas
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


# views.py
import uuid
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from .forms import PasswordResetRequestForm
from django.utils.html import strip_tags

from .models import Usuario  # O get_user_model()
from email.mime.image import MIMEImage
from django.conf import settings
import os

from django.shortcuts import render
from .models import Jugador


def es_admin(user):
    return user.is_authenticated and user.is_staff

def index(request):
    return HttpResponse('Hello, world')

# INICIO DE SESION Y REGISTRO

from django.shortcuts import render
from .models import Jugador

def inicio_view(request):
    jugadores = Jugador.objects.all()
    return render(request, 'inicio.html', {
        'jugadores': jugadores,
        # demás contexto…
    })


def registro_view(request):
    translation.activate('es')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('inicio')
    else:
        form = RegistroForm()
    return render(request, 'Registro.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('inicio')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('inicio')

from django.http import JsonResponse
from .models import Usuario

def verificar_email(request):
    email = request.GET.get('email')
    existe = Usuario.objects.filter(email=email).exists()
    return JsonResponse({'exists': existe})

# ====== FIN DE SESION Y REGISTRO ======


# TIENDA Y PRODUCTOS
def tienda_view(request):
    productos = Producto.objects.all()
    camisetas = productos.filter(tipo='Camiseta')
    sudaderas = productos.filter(tipo='Sudadera')
    equipaciones = productos.filter(tipo='Equipación')
    config = get_configuracion()
    return render(request, 'Tienda.html', {
        'camisetas': camisetas,
        'sudaderas': sudaderas,
        'equipaciones': equipaciones,
        'config': config,
    })


def detalle_producto_view(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    return render(request, 'detalle_producto.html', {'producto': producto})


@login_required
def añadir_al_carrito_view(request, producto_id):
    """
    - Si el producto es de tipo 'Equipación', leemos 'compra_tipo' (solo_camiseta o completo).
      • solo_camiseta -> precio fijo 22.00 € y no se guardan dorsales.
      • completo      -> precio = producto.precio y se guardan dorsales.
    - Para camisetas/sudaderas, comportamiento normal: precio = producto.precio.
    """
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)
        carrito = request.session.get('carrito', [])

        # Siempre pedimos la talla
        talla = request.POST.get('talla')

        # Inicializar valores por defecto
        precio_item = float(producto.precio)
        nombre_dorsal = ''
        numero_dorsal = None

        # Si es equipación, miramos la opción de compra
        if producto.tipo == 'Equipación':
            compra_tipo = request.POST.get('compra_tipo', 'solo_camiseta')
            if compra_tipo == 'solo_camiseta':
                precio_item = 22.00
                nombre_dorsal = request.POST.get('nombre_dorsal', '') or ''
                numero_dorsal_raw = request.POST.get('numero_dorsal')
                numero_dorsal = int(numero_dorsal_raw) if numero_dorsal_raw else None
            else:
                # Equipación completa: tomamos precio original y dorsales
                precio_item = float(producto.precio)
                nombre_dorsal = request.POST.get('nombre_dorsal', '') or ''
                numero_dorsal_raw = request.POST.get('numero_dorsal')
                numero_dorsal = int(numero_dorsal_raw) if numero_dorsal_raw else None
        else:
            # No es equipación: precio estándar
            precio_item = float(producto.precio)

        # Construimos el ítem que se guardará en sesión
        tipo_real = (
        'Camiseta' if producto.tipo == 'Equipación' and request.POST.get('compra_tipo') == 'solo_camiseta'
        else producto.tipo
        )
        
        item = {
        'producto_id': producto.id,
        'nombre': producto.nombre,
        'precio': precio_item,
        'talla': talla,
        'tipo': tipo_real,  # 👈 usamos el tipo real ajustado
        'compra_tipo': request.POST.get('compra_tipo') if producto.tipo == 'Equipación' else None,
        'nombre_dorsal': nombre_dorsal,
        'numero_dorsal': numero_dorsal,
        }

        carrito.append(item)
        request.session['carrito'] = carrito

        return redirect(reverse('detalle_producto', args=[producto.id]) + '?añadido=ok')

    # Si no es POST, redirigimos de nuevo a la página de detalle
    return redirect('detalle_producto', producto_id)

# - Ver carrito
@login_required
def carrito_view(request):
    raw_carrito = request.session.get('carrito', [])
    carrito = []
    for item in raw_carrito:
        producto = Producto.objects.get(id=item['producto_id'])
        item['imagen_url'] = producto.imagen.url
        # NO sobreescribimos item['tipo'] aquí para respetar el 'tipo_real' guardado en sesión
        carrito.append(item)

    if request.method == "GET":
        if 'aplicar_descuento' in request.GET:
            request.session['aplicar_descuento'] = request.GET.get('aplicar_descuento') == '1'
        elif 'aplicar_descuento' not in request.GET:
            request.session['aplicar_descuento'] = False  # se apagó el toggle

    aplicar_descuento = request.session.get('aplicar_descuento', False)

    num_solo = sum(1 for item in carrito if item.get('compra_tipo') == 'solo_camiseta')
    if num_solo >= 2:
        mostrar_descuento = True
    else:
        mostrar_descuento = False

    
    # Marcar qué camisetas reciben descuento (solo pares)
    solo_idxs = [i for i, it in enumerate(carrito) if it.get('compra_tipo') == 'solo_camiseta']
    # cuántas camisetas (de esos) tendrán descuento: pares completos
    num_descuento = (len(solo_idxs) // 2) * 2 if aplicar_descuento else 0
    # recorrer esos índices y marcar True solo para los primeros num_descuento
    for pos, idx in enumerate(solo_idxs):
        carrito[idx]['con_descuento'] = (pos < num_descuento)
    # Las demás (no camisetas o sobrantes) quedan con con_descuento=False por defecto
    for i, it in enumerate(carrito):
        if it.get('compra_tipo') != 'solo_camiseta':
            carrito[i]['con_descuento'] = False

    if aplicar_descuento:
        total = calcular_total_carrito(carrito)  # ✅ con descuento
        total_sin_descuento = sum(Decimal(item['precio']) for item in carrito)
        ahorro = total_sin_descuento - total
        posible_ahorro = 0
    else:
        total = sum(Decimal(item['precio']) for item in carrito)  # ✅ sin descuento
        ahorro = 0
        posible_ahorro = total - calcular_total_carrito(carrito)

    config = get_configuracion()
    return render(request, 'carrito.html', {
        'carrito': carrito,
        'total': total,
        'ahorro': ahorro,
        'aplicar_descuento': aplicar_descuento,
        'posible_ahorro': posible_ahorro,
        'mostrar_descuento': mostrar_descuento,
        'pedidos_abiertos': config.pedidos_abiertos,
    })


# ELIMINAR, EDITAR Y VACÍO DEL CARRITO
@require_POST
@login_required
def eliminar_del_carrito_view(request, item_index):
    carrito = request.session.get('carrito', [])
    try:
        carrito.pop(item_index)
        request.session['carrito'] = carrito
    except IndexError:
        pass
    return redirect('carrito')


@require_POST
@login_required
def editar_item_carrito_view(request, item_index):
    carrito = request.session.get('carrito', [])
    try:
        item = carrito[item_index]
        item['talla'] = request.POST.get('talla')
        if item.get('nombre_dorsal') is not None:
            item['nombre_dorsal'] = request.POST.get('nombre_dorsal')
            item['numero_dorsal'] = request.POST.get('numero_dorsal')
        carrito[item_index] = item
        request.session['carrito'] = carrito
    except IndexError:
        pass
    return redirect('carrito')


@require_POST
@login_required
def vaciar_carrito_view(request):
    request.session['carrito'] = []
    return redirect('carrito')

### ============ FIN ACCIONES DEL CARRITO ============ ###

### ============ GESTION DE PEDIDOS ============ ### 
@login_required
def resumen_pedido_view(request):
    raw_carrito = request.session.get('carrito', [])
    resumen = []
    aplicar_descuento = request.session.get('aplicar_descuento', False)

    for item in raw_carrito:
        try:
            producto = Producto.objects.get(id=item['producto_id'])
            item['imagen_url'] = producto.imagen.url

            # ✅ Ajustar tipo si es solo camiseta
            if producto.tipo == "Equipación" and item.get('compra_tipo') == "solo_camiseta":
                item['tipo'] = "Camiseta"
            else:
                item['tipo'] = producto.tipo

            resumen.append(item)
        except Producto.DoesNotExist:
            continue

    total = (
        calcular_total_carrito(resumen)
        if aplicar_descuento
        else sum(Decimal(item['precio']) for item in resumen)
    )

    request.session['resumen_pedido'] = resumen

    return render(request, 'resumen_pedido.html', {
        'resumen': resumen,
        'total': total
    })


from decimal import Decimal

@login_required
def confirmar_pedido_view(request):
    carrito = request.session.get('carrito', [])
    usar_descuento = request.session.get('aplicar_descuento', False)

    if not carrito:
        return redirect('carrito')

    pedido = Pedido.objects.create(usuario=request.user, pagado=False, usar_descuento=usar_descuento)

    for item in carrito:
        producto = Producto.objects.get(id=item['producto_id'])
        numero_dorsal_raw = item.get('numero_dorsal')
        numero_dorsal = int(numero_dorsal_raw) if numero_dorsal_raw else None

        LineaPedido.objects.create(
            pedido=pedido,
            producto=producto,
            talla=item['talla'],
            nombre_dorsal=item.get('nombre_dorsal') or '',
            numero_dorsal=numero_dorsal,
            compra_tipo=item.get('compra_tipo')
        )

    # Limpiar sesión
    del request.session['carrito']
    request.session.pop('aplicar_descuento', None)

    # Calcular total con o sin descuento
    carrito_items = []
    for linea in pedido.lineas.all():
        if linea.compra_tipo == 'solo_camiseta':
            precio_real = 22.00
        else:
            precio_real = float(linea.producto.precio)

        carrito_items.append({
            'precio': precio_real,
            'tipo': 'Camiseta' if linea.compra_tipo == 'solo_camiseta' else linea.producto.tipo,
            'compra_tipo': linea.compra_tipo
        })


    total = calcular_total_carrito(carrito_items)

    print(f"Total del pedido: {total} €")

    enviar_confirmacion_pedido(request.user, pedido)

    return render(request, 'pedido_confirmado.html', {
        'pedido': pedido,
        'total': total
    })




@login_required
def pago_simulado_view(request):
    resumen = request.session.get('resumen_pedido')
    if not resumen:
        return redirect('carrito')
    pedido = Pedido.objects.create(usuario=request.user, pagado=False)
    for item in resumen:
        producto = Producto.objects.get(id=item['producto_id'])
        numero_dorsal_raw = item.get('numero_dorsal')
        numero_dorsal = int(numero_dorsal_raw) if numero_dorsal_raw else None
        LineaPedido.objects.create(
            pedido=pedido,
            producto=producto,
            talla=item['talla'],
            nombre_dorsal=item.get('nombre_dorsal') or '',
            numero_dorsal=numero_dorsal
        )
    request.session.pop('resumen_pedido', None)
    request.session.pop('carrito', None)
    enviar_confirmacion_pedido(request.user, pedido)
    return render(request, 'pedido_confirmado.html', {'pedido': pedido})


def enviar_confirmacion_pedido(usuario, pedido):
    subject = f"✅ Pedido #{pedido.id} confirmado - Relámpago Pricense FC"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [usuario.email]

    # Renderizamos el HTML de la confirmación
    html_content = render_to_string('emails/confirmacion_pedido.html', {
        'usuario': usuario,
        'pedido': pedido,
    })

    # Creamos el mensaje multi-parte
    mensaje = EmailMultiAlternatives(
        subject=subject,
        body="Gracias por tu pedido en Relámpago Pricense FC.",  # texto plano opcional
        from_email=from_email,
        to=to,
    )
    mensaje.attach_alternative(html_content, "text/html")

    # Adjuntamos el escudo para que funcione <img src="cid:logo_escudo">
    logo_path = os.path.join(settings.BASE_DIR, 'relampagoweb', 'static', 'img', 'escudo.png')
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-ID', '<logo_escudo>')
            img.add_header('Content-Disposition', 'inline', filename='escudo.png')
            mensaje.attach(img)

    # Enviamos
    mensaje.send(fail_silently=False)


def calcular_total_carrito(carrito):
    
    from decimal import Decimal

    total = Decimal('0.00')
    camisetas = []

    for item in carrito:
        if item.get('compra_tipo') == 'solo_camiseta':
            camisetas.append(item)
        else:
            total += Decimal(item['precio'])

    num_camisetas = len(camisetas)
    pares = num_camisetas // 2
    sueltas = num_camisetas % 2

    if num_camisetas == 1:
        total = Decimal('22.00')  # Si solo hay una camiseta, precio fijo
    else:
        total += Decimal(pares * 2) * Decimal('20.00') + Decimal(sueltas) * Decimal('22.00')


    return total


def enviar_email_pago_confirmado(pedido):
    subject = f"Pago confirmado del pedido #{pedido.id} en Relámpago Pricense FC"
    html_content = render_to_string('emails/pedido_pagado.html', {
        'pedido': pedido,
        'usuario': pedido.usuario,
    })

    email = EmailMultiAlternatives(
        subject=subject,
        body="Hemos recibido tu pago. Gracias por confiar en Relámpago Pricense FC.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[pedido.usuario.email]
    )
    email.attach_alternative(html_content, "text/html")

    # Adjuntar el escudo
    escudo_path = os.path.join(settings.BASE_DIR, 'relampagoweb', 'static', 'img', 'escudo.png')
    if os.path.exists(escudo_path):
        with open(escudo_path, 'rb') as f:
            image = MIMEImage(f.read())
            image.add_header('Content-ID', '<logo_escudo>')
            email.attach(image)

    email.send()

### ============ FIN GESTION DE PEDIDOS ============ ###


### ============ ADMINISTRACIÓN DE PEDIDOS ============ ###

@user_passes_test(es_admin)
def exportar_pedidos_excel(request):
    pedidos = Pedido.objects.prefetch_related('lineas__producto').filter(pagado=True)
    datos = []
    for pedido in pedidos:
        for linea in pedido.lineas.all():
            datos.append({
                'Nº Pedido': pedido.id,
                'Nombre': pedido.usuario.name,
                'Email': pedido.usuario.email,
                'Producto': linea.producto.nombre,
                'Tipo': 'Camiseta' if linea.compra_tipo == 'solo_camiseta' else linea.producto.tipo,
                'Talla': linea.talla,
                'Nombre dorsal': linea.nombre_dorsal or '',
                'Dorsal': linea.numero_dorsal or '',
            })
    df = pd.DataFrame(datos)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=pedidos.xlsx'
    df.to_excel(response, index=False)
    return response


@user_passes_test(es_admin)
def lista_pedidos_view(request):
    pedidos = Pedido.objects.all().order_by('-usuario__name')
    config = get_configuracion()
    return render(request, 'admin/lista_pedidos.html', {
        'pedidos': pedidos,
        'config': config
    })


@user_passes_test(es_admin)
def cambiar_estado_pedido(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, id=pedido_id)
        estaba_no_pagado = not pedido.pagado  # Guardamos el estado anterior
        pedido.pagado = not pedido.pagado
        pedido.save()

        if estaba_no_pagado and pedido.pagado:
            enviar_email_pago_confirmado(pedido)  # ✉️ Enviar solo si ahora está pagado

    return redirect('lista_pedidos')


@user_passes_test(es_admin)
def detalle_pedido_admin_view(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'admin/detalle_pedido.html', {'pedido': pedido})


def get_configuracion():
    config, created = Configuracion.objects.get_or_create(id=1)
    return config


## MANDAR CORREO PARA ABRIR PEDIDOS ###
@staff_member_required
def alternar_pedidos_view(request):
    config = get_configuracion()
    config.pedidos_abiertos = not config.pedidos_abiertos
    config.save()

    # Solo si acabamos de abrir los pedidos
    if config.pedidos_abiertos:
        usuarios = get_user_model().objects.filter(email__isnull=False)
        asunto = "🟢 ¡Se han abierto los pedidos!"
        tienda_url = request.build_absolute_uri(reverse('tienda'))

        for usuario in usuarios:
            html_content = render_to_string('emails/pedidos_abiertos.html', {
                'usuario': usuario,
                'tienda_url': tienda_url,
            })

            email = EmailMultiAlternatives(
                subject=asunto,
                body="Ve nuestra tienda online para más información.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[usuario.email]
            )
            email.attach_alternative(html_content, "text/html")

            # Adjuntar escudo inline
            escudo_path = os.path.join(settings.BASE_DIR, 'relampagoweb', 'static', 'img', 'escudo.png')
            if os.path.exists(escudo_path):
                with open(escudo_path, 'rb') as f:
                    logo = MIMEImage(f.read())
                    logo.add_header('Content-ID', '<logo_escudo>')
                    email.attach(logo)

            email.send()

    return redirect('lista_pedidos')



@user_passes_test(es_admin)
def panel_pedidos_view(request):
    pedidos = Pedido.objects.all().order_by('-fecha')
    pedidos_abiertos = get_configuracion().pedidos_abiertos
    return render(request, 'panel_pedidos.html', {
        'pedidos': pedidos,
        'pedidos_abiertos': pedidos_abiertos,
    })







reset_tokens = {}  # Diccionario para almacenar tokens de restablecimiento de contraseña

def solicitar_reset_password(request):
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = Usuario.objects.get(email=email)
                token = str(uuid.uuid4())
                reset_tokens[token] = user.id  # ⚠️ Sustituir por modelo/token seguro en producción

                # Generar enlace
                enlace = request.build_absolute_uri(f"/reset-password/{token}/")

                # Renderizar plantilla HTML
                html_content = render_to_string("emails/password_reset_email.html", {
                    "user": user,
                    "enlace": enlace
                })
                text_content = strip_tags(html_content)

                # Enviar email
                msg = EmailMultiAlternatives(
                    subject="🔐 Recuperación de contraseña",
                    body=text_content,
                    from_email="noreply@berural.com",
                    to=[email]
                )
                msg.attach_alternative(html_content, "text/html")
                # Ruta absoluta al logo
                logo_path = os.path.join(settings.BASE_DIR, 'relampagoweb', 'static', 'img', 'escudo.png')
                with open(logo_path, 'rb') as f:
                    logo = MIMEImage(f.read())
                    logo.add_header('Content-ID', '<logo_escudo>')
                    msg.attach(logo)
                msg.send()

                return render(request, "Contrasena/mensaje_enviado.html")
            except Usuario.DoesNotExist:
                form.add_error('email', 'No existe un usuario con ese correo.')
    else:
        form = PasswordResetRequestForm()
    return render(request, "Contrasena/solicitar_reset_password.html", {"form": form})


# views.py
from .forms import CambiarPasswordForm

def resetear_password(request, token):
    user_id = reset_tokens.get(token)
    if not user_id:
        raise Http404("Token no válido o expirado")

    usuario = Usuario.objects.get(id=user_id)

    if request.method == "POST":
        form = CambiarPasswordForm(request.POST)
        if form.is_valid():
            usuario.set_password(form.cleaned_data['password'])
            usuario.save()
            del reset_tokens[token]
            return redirect("login")
    else:
        form = CambiarPasswordForm()

    return render(request, "Contrasena/password_reset.html", {"form": form})