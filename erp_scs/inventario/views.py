# inventario/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, F
from .models import Producto, Categoria, Lote, MovimientoInventario
from .forms import ProductoForm, AjusteInventarioForm

@login_required
def inventario_home(request):
    context = {
        'total_productos': Producto.objects.filter(activo=True).count(),
        'productos_bajo_stock': Producto.objects.filter(
            stock_actual__lt=F('stock_minimo'),
            activo=True
        ).count(),
        'lotes_pendientes': Lote.objects.filter(
            estado='PENDIENTE'
        ).count()
    }
    return render(request, 'inventario/home.html', context)

@login_required
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto {producto.nombre} creado exitosamente')
            return redirect('inventario:home')
    else:
        form = ProductoForm()
    
    return render(request, 'inventario/crear_producto.html', {'form': form})

@login_required
def consultar_stock(request):
    query = request.GET.get('q', '')
    categoria = request.GET.get('categoria', '')
    
    productos = Producto.objects.filter(activo=True)
    
    if query:
        productos = productos.filter(
            Q(codigo__icontains=query) |
            Q(nombre__icontains=query)
        )
    
    if categoria:
        productos = productos.filter(categoria__tipo=categoria)
    
    context = {
        'productos': productos,
        'categorias': Categoria.TIPO_CHOICES,
        'query': query,
        'categoria_seleccionada': categoria
    }
    return render(request, 'inventario/consultar_stock.html', context)

@login_required
def ajuste_inventario(request):
    if request.method == 'POST':
        form = AjusteInventarioForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data['producto']
            cantidad = form.cleaned_data['cantidad']
            tipo_movimiento = form.cleaned_data['tipo_movimiento']
            descripcion = form.cleaned_data['descripcion']
            
            # Guardar el stock anterior
            stock_anterior = producto.stock_actual
            
            # Calcular el stock resultante
            if tipo_movimiento == 'ENTRADA':
                stock_resultante = stock_anterior + cantidad
            elif tipo_movimiento == 'SALIDA':
                stock_resultante = stock_anterior - cantidad
            else:  # AJUSTE
                stock_resultante = cantidad
            
            # Crear el movimiento con los stocks
            MovimientoInventario.objects.create(
                producto=producto,
                tipo_movimiento=tipo_movimiento,
                cantidad=cantidad,
                descripcion=descripcion,
                usuario=request.user,
                stock_anterior=stock_anterior,
                stock_resultante=stock_resultante
            )
            
            # Actualizar el stock del producto
            producto.stock_actual = stock_resultante
            producto.save()
            
            
            messages.success(request, 'Ajuste de inventario realizado exitosamente')
            return redirect('inventario:consultar_stock')
    else:
        producto_id = request.GET.get('producto_id')
        initial_data = {}
        if producto_id:
            try:
                producto = Producto.objects.get(id=producto_id)
                initial_data['producto'] = producto
            except Producto.DoesNotExist:
                pass
        form = AjusteInventarioForm(initial=initial_data)
    
    return render(request, 'inventario/ajuste_inventario.html', {'form': form})
@login_required
def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    movimientos = MovimientoInventario.objects.filter(
        producto=producto
    ).order_by('-fecha_movimiento')[:10]
    
    context = {
        'producto': producto,
        'movimientos': movimientos
    }
    return render(request, 'inventario/detalle_producto.html', context)

@login_required
def historial_movimientos(request):
    # Parámetros de filtrado
    producto_id = request.GET.get('producto')
    tipo_movimiento = request.GET.get('tipo_movimiento')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    query = request.GET.get('q', '')

    # Query base
    movimientos = MovimientoInventario.objects.select_related(
        'producto', 
        'usuario'
    ).order_by('-fecha_movimiento')

    # Aplicar filtros
    if producto_id:
        movimientos = movimientos.filter(producto_id=producto_id)
    
    if tipo_movimiento:
        movimientos = movimientos.filter(tipo_movimiento=tipo_movimiento)
    
    if fecha_desde:
        movimientos = movimientos.filter(fecha_movimiento__date__gte=fecha_desde)
    
    if fecha_hasta:
        movimientos = movimientos.filter(fecha_movimiento__date__lte=fecha_hasta)
    
    if query:
        movimientos = movimientos.filter(
            Q(producto__nombre__icontains=query) |
            Q(producto__codigo__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(documento_referencia__icontains=query)
        )

    context = {
        'movimientos': movimientos,
        'productos': Producto.objects.filter(activo=True),
        'tipos_movimiento': MovimientoInventario.TIPO_MOVIMIENTO_CHOICES,
        'filtros': {
            'producto_id': producto_id,
            'tipo_movimiento': tipo_movimiento,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'query': query
        }
    }
    
    return render(request, 'inventario/historial_movimientos.html', context)
