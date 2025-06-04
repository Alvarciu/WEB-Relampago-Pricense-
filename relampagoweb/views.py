from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
import pandas as pd
from .forms import RegistroForm, LoginForm
from .models import Producto, Pedido, LineaPedido, Configuracion, get_configuracion
from django.contrib.auth import get_user_model
from django.core.mail import send_mass_mail
from decimal import Decimal



def es_admin(user):
    return user.is_authenticated and user.is_staff

def index(request):
    return HttpResponse('Hello, world')

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

def tienda_view(request):
    productos = Producto.objects.all()
    equipaciones = productos.filter(tipo='equipacion')
    sudaderas = productos.filter(tipo='sudadera')
    return render(request, 'tienda.html', {
        'equipaciones': equipaciones,
        'sudaderas': sudaderas,
    })

def detalle_producto_view(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    return render(request, 'detalle_producto.html', {'producto': producto})

def añadir_al_carrito_view(request, producto_id):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)
        carrito = request.session.get('carrito', [])
        item = {
            'producto_id': producto.id,
            'nombre': producto.nombre,
            'precio': float(producto.precio),
            'talla': request.POST.get('talla'),
        }
        if producto.tipo == 'equipacion':
            item['nombre_dorsal'] = request.POST.get('nombre_dorsal')
            item['numero_dorsal'] = request.POST.get('numero_dorsal')
        carrito.append(item)
        request.session['carrito'] = carrito
        return redirect(reverse('detalle_producto', args=[producto.id]) + '?añadido=ok')

@login_required
def carrito_view(request):
    raw_carrito = request.session.get('carrito', [])
    carrito = []
    for item in raw_carrito:
        producto = Producto.objects.get(id=item['producto_id'])
        item['imagen_url'] = producto.imagen.url
        item['tipo'] = producto.tipo
        carrito.append(item)

    aplicar_descuento = request.GET.get('aplicar_descuento') == '1'

    if aplicar_descuento:
        total = calcular_total_carrito(carrito)  # con descuento
        total_sin_descuento = sum(Decimal(item['precio']) for item in carrito)
        ahorro = total_sin_descuento - total
        posible_ahorro = ahorro
    else:
        ahorro = 0
        total = calcular_total_carrito(carrito)  # con descuento
        total_sin_descuento = sum(Decimal(item['precio']) for item in carrito)
        posible_ahorro =  total_sin_descuento - total


    config = get_configuracion()
    return render(request, 'carrito.html', {
        'carrito': carrito,
        'total': total,
        'ahorro': ahorro,
        'aplicar_descuento': aplicar_descuento,
        'posible_ahorro': posible_ahorro,
        'pedidos_abiertos': config.pedidos_abiertos,
    })

# def carrito_view(request):
#     raw_carrito = request.session.get('carrito', [])
#     carrito = []
#     for item in raw_carrito:
#         producto = Producto.objects.get(id=item['producto_id'])
#         item['imagen_url'] = producto.imagen.url
#         item['tipo'] = producto.tipo  # <- Asegúrate de que cada item tenga el tipo
#         carrito.append(item)

#     total = calcular_total_carrito(carrito)  # ← aquí aplicas el descuento

#     config = get_configuracion()
#     return render(request, 'carrito.html', {
#         'carrito': carrito,
#         'total': total,
#         'pedidos_abiertos': config.pedidos_abiertos,
#     })

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
        pedido.pagado = not pedido.pagado
        pedido.save()
    return redirect('lista_pedidos')

@user_passes_test(es_admin)
def detalle_pedido_admin_view(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'admin/detalle_pedido.html', {'pedido': pedido})

def get_configuracion():
    config, created = Configuracion.objects.get_or_create(id=1)
    return config

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

@login_required
def resumen_pedido_view(request):
    raw_carrito = request.session.get('carrito', [])
    resumen = []
    total = 0
    for item in raw_carrito:
        try:
            producto = Producto.objects.get(id=item['producto_id'])
            item['imagen_url'] = producto.imagen.url
            resumen.append(item)
            total += item['precio']
        except Producto.DoesNotExist:
            continue
    request.session['resumen_pedido'] = resumen
    return render(request, 'resumen_pedido.html', {
        'resumen': resumen,
        'total': total
    })

@login_required
def confirmar_pedido_view(request):
    carrito = request.session.get('carrito', [])
    if not carrito:
        return redirect('carrito')
    pedido = Pedido.objects.create(usuario=request.user, pagado=False)
    for item in carrito:
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
    del request.session['carrito']
    asunto = f"Confirmación de tu pedido #{pedido.id} en Relámpago Pricense FC"
    mensaje = render_to_string('emails/confirmacion_pedido.txt', {
        'pedido': pedido,
        'usuario': request.user,
        'lineas': pedido.lineas.all(),
        'total': pedido.total
    })
    send_mail(
        subject=asunto,
        message=mensaje,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[request.user.email],
        fail_silently=False,
    )
    return render(request, 'pedido_confirmado.html', {'pedido': pedido})

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
        if item.get('tipo') == 'equipacion':
            camisetas.append(item)
        else:
            total += Decimal(item['precio'])

    num_camisetas = len(camisetas)
    pares = num_camisetas // 2
    sueltas = num_camisetas % 2

    total += Decimal(pares * 2) * Decimal('20.00') + Decimal(sueltas) * Decimal('22.00')

    return total
