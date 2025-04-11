from django.shortcuts import render, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import RegistroForm, LoginForm
from .models import Producto
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, get_object_or_404
from .models import Producto
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import pandas as pd
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .models import Pedido
from django.conf import settings
from .models import Configuracion
from .models import get_configuracion




# Create your views here.
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
    return render(request, 'tienda.html', {'productos': productos})

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

        # Solo si es equipación, añadimos personalización
        if producto.tipo == 'equipacion':
            item['nombre_dorsal'] = request.POST.get('nombre_dorsal')
            item['numero_dorsal'] = request.POST.get('numero_dorsal')

        carrito.append(item)
        request.session['carrito'] = carrito

        return redirect('tienda')  # O a 'carrito' si ya lo tuvieras

@login_required
def carrito_view(request):
    raw_carrito = request.session.get('carrito', [])
    carrito = []

    total = 0
    for item in raw_carrito:
        producto = Producto.objects.get(id=item['producto_id'])
        item['imagen_url'] = producto.imagen.url
        carrito.append(item)
        total += item['precio']

    config = get_configuracion()

    return render(request, 'carrito.html', {
        'carrito': carrito,
        'total': total,
        'pedidos_abiertos': config.pedidos_abiertos,
    })


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


@staff_member_required
def exportar_pedidos_excel(request):
    pedidos = Pedido.objects.prefetch_related('lineas__producto').all()
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


@staff_member_required
def lista_pedidos_view(request):
    pedidos = Pedido.objects.all().order_by('-fecha')
    config = get_configuracion()
    return render(request, 'admin/lista_pedidos.html', {
        'pedidos': pedidos,
        'config': config  # 👈 aquí estás pasándola al HTML
    })

@staff_member_required
def detalle_pedido_admin_view(request, pedido_id):
    pedido = Pedido.objects.get(id=pedido_id)
    return render(request, 'admin/detalle_pedido.html', {'pedido': pedido})


def get_configuracion():
    config, created = Configuracion.objects.get_or_create(id=1)
    return config

@staff_member_required
def alternar_pedidos_view(request):
    config = get_configuracion()
    config.pedidos_abiertos = not config.pedidos_abiertos
    config.save()
    return redirect('lista_pedidos')
