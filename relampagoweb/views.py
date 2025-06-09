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


def es_admin(user):
    return user.is_authenticated and user.is_staff

def index(request):
    return HttpResponse('Hello, world')

# INICIO DE SESION Y REGISTRO
def inicio_view(request):
    return render(request, 'inicio.html')

def registro_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('inicio')
    else:
        form = RegistroForm()
    return render(request, 'registro.html', {'form': form})

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
    return redirect('login')

# ====== FIN DE SESION Y REGISTRO ======




# TIENDA Y PRODUCTOS
def tienda_view(request):
    productos = Producto.objects.all()
    camisetas = productos.filter(tipo='Camiseta')
    sudaderas = productos.filter(tipo='Sudadera')
    equipaciones = productos.filter(tipo='Equipación')
    config = get_configuracion()
    return render(request, 'tienda.html', {
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




#==========  ACCIONES DEL CARRITO ===========
# - Ver carrito
# @login_required
# def carrito_view(request):
#     raw_carrito = request.session.get('carrito', [])
#     carrito = []
#     for item in raw_carrito:
#         producto = Producto.objects.get(id=item['producto_id'])
#         item['imagen_url'] = producto.imagen.url
#         item['tipo'] = producto.tipo
#         carrito.append(item)
#     if request.method == "GET":
#         if 'aplicar_descuento' in request.GET:
#             request.session['aplicar_descuento'] = request.GET.get('aplicar_descuento') == '1'
#         elif 'aplicar_descuento' not in request.GET:
#             request.session['aplicar_descuento'] = False  # se apagó el toggle
#     aplicar_descuento = request.session.get('aplicar_descuento', False)
#     if aplicar_descuento:
#         total = calcular_total_carrito(carrito)  # ✅ con descuento
#         total_sin_descuento = sum(Decimal(item['precio']) for item in carrito)
#         ahorro = total_sin_descuento - total
#         posible_ahorro = 0
#     else:
#         total = sum(Decimal(item['precio']) for item in carrito)  # ✅ sin descuento
#         ahorro = 0
#         posible_ahorro = total - calcular_total_carrito(carrito)
#     config = get_configuracion()
#     return render(request, 'carrito.html', {
#         'carrito': carrito,
#         'total': total,
#         'ahorro': ahorro,
#         'aplicar_descuento': aplicar_descuento,
#         'posible_ahorro': posible_ahorro,
#         'pedidos_abiertos': config.pedidos_abiertos,
#     })


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

# @login_required
# def confirmar_pedido_view(request):
#     carrito = request.session.get('carrito', [])
#     usar_descuento = request.session.get('aplicar_descuento', False)


#     if not carrito:
#         return redirect('carrito')

#     pedido = Pedido.objects.create(usuario=request.user, pagado=False, usar_descuento=usar_descuento)

#     for item in carrito:
#         producto = Producto.objects.get(id=item['producto_id'])
#         numero_dorsal_raw = item.get('numero_dorsal')
#         numero_dorsal = int(numero_dorsal_raw) if numero_dorsal_raw else None

#         LineaPedido.objects.create(
#             pedido=pedido,
#             producto=producto,
#             talla=item['talla'],
#             nombre_dorsal=item.get('nombre_dorsal') or '',
#             numero_dorsal=numero_dorsal,
#             compra_tipo=item.get('compra_tipo')
#         )

#     # Limpiar sesión
#     del request.session['carrito']
#     request.session.pop('usar_descuento', None)

#     # Calcular total con o sin descuento usando el campo compra_tipo
#     carrito_items = []
#     for linea in pedido.lineas.all():
#         # Aseguramos el precio correcto según tipo de compra
#         if linea.compra_tipo == 'solo_camiseta':
#             precio_real = 22.00
#         else:
#             precio_real = float(linea.producto.precio)

#         carrito_items.append({
#             'precio': precio_real,
#             'tipo': 'Camiseta' if linea.compra_tipo == 'solo_camiseta' else linea.producto.tipo,
#             'compra_tipo': linea.compra_tipo
#         })


#     # Preparar y enviar correo como antes...
#     # (Aquí puedes dejar el bloque de envío de correo exactamente igual)

#     return render(request, 'pedido_confirmado.html', {
#         'pedido': pedido,
#         'total': total
#     })

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

    if usar_descuento:
        total = calcular_total_carrito(carrito_items)
    else:
        total = sum(Decimal(item['precio']) for item in carrito_items)

    return render(request, 'pedido_confirmado.html', {
        'pedido': pedido,
        'total': total
    })


# # Limpiar sesión
# del request.session['carrito']
# request.session.pop('usar_descuento', None)

# # Calcular total con o sin descuento
# carrito_items = []
# for linea in pedido.lineas.all():
#     carrito_items.append({
#         'precio': float(linea.producto.precio),
#         'tipo': linea.producto.tipo,
#         'compra_tipo': 'solo_camiseta' if not linea.nombre_dorsal else 'completo'
#     })

# if usar_descuento:
#     total = calcular_total_carrito(carrito_items)
# else:
#     total = sum(Decimal(item['precio']) for item in carrito_items)

# # Preparar correo
# asunto = f"Confirmación de tu pedido #{pedido.id} en Relámpago Pricense FC"
# html_content = render_to_string('emails/confirmacion_pedido.html', {
#     'pedido': pedido,
#     'usuario': request.user,
# })

# email = EmailMultiAlternatives(
#     subject=asunto,
#     body="Gracias por tu pedido. Consulta los detalles en la versión HTML.",
#     from_email=settings.DEFAULT_FROM_EMAIL,
#     to=[request.user.email]
# )
# email.attach_alternative(html_content, "text/html")

# logo_path = os.path.join(settings.BASE_DIR, 'relampagoweb', 'static', 'img', 'escudo.png')
# if os.path.exists(logo_path):
#     with open(logo_path, 'rb') as f:
#         logo = MIMEImage(f.read())
#         logo.add_header('Content-ID', '<logo_escudo>')
#         logo.add_header('Content-Disposition', 'inline')
#         email.attach(logo)

# email.send()

# return render(request, 'pedido_confirmado.html', {
#     'pedido': pedido,
#     'total': total
# })



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
    asunto = f"✅ Pedido #{pedido.id} confirmado - Relámpago Pricense FC"
    remitente = settings.DEFAULT_FROM_EMAIL
    destinatario = [usuario.email]
    html_content = render_to_string("emails/confirmacion_pedido.html", {
        "usuario": usuario,
        "pedido": pedido,
    })
    mensaje = EmailMultiAlternatives(asunto, "", remitente, destinatario)
    mensaje.attach_alternative(html_content, "text/html")
    mensaje.send()


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

    if config.pedidos_abiertos:
        usuarios = get_user_model().objects.all()
        mensajes = []
        for usuario in usuarios:
            if usuario.email:
                asunto = "🟢 ¡Se han abierto los pedidos!"
                mensaje = (
                    f"Hola {usuario.name},\n\n"
                    f"Ya puedes hacer tu pedido en Relámpago Pricense FC desde nuestra tienda online.\n"
                    f"No pierdas la oportunidad de conseguir tu camiseta personalizada.\n\n"
                    f"👉 Entra ya en: http://127.0.0.1:8000/tienda/\n\n"
                    f"¡Gracias por tu apoyo!\n"
                )
                mensajes.append((asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [usuario.email]))
        send_mass_mail(mensajes, fail_silently=True)

    return redirect('lista_pedidos')


@user_passes_test(es_admin)
def panel_pedidos_view(request):
    pedidos = Pedido.objects.all().order_by('-fecha')
    pedidos_abiertos = get_configuracion().pedidos_abiertos
    return render(request, 'panel_pedidos.html', {
        'pedidos': pedidos,
        'pedidos_abiertos': pedidos_abiertos,
    })


