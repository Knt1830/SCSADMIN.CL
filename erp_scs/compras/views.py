# compras/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Max
from django.db import transaction
from django.core.paginator import Paginator
from datetime import datetime, date
from decimal import Decimal
from django.forms import inlineformset_factory
from .models import (
    TipoProveedor, Proveedor, ProveedorProducto,
    OrdenCompra, DetalleOrdenCompra,
)

from inventario.models import Producto, MovimientoInventario

from .forms import (
    TipoProveedorForm, ProveedorForm, ProveedorProductoForm,
    OrdenCompraForm, DetalleOrdenCompraForm,
)

@login_required
def compras_home(request):
    context = {
        'total_proveedores': Proveedor.objects.filter(activo=True).count(),
        'proveedores_mp': Proveedor.objects.filter(
            tipo_proveedor__es_materia_prima=True,
            activo=True
        ).count(),
        'ordenes_pendientes': OrdenCompra.objects.filter(
            estado__in=['BORRADOR', 'ENVIADA', 'CONFIRMADA']
        ).count()
    }
    return render(request, 'compras/home.html', context)

@login_required
def crear_proveedor(request):
    ProductoFormSet = inlineformset_factory(
        Proveedor,
        ProveedorProducto,
        form=ProveedorProductoForm,
        extra=1,
        can_delete=True,
        min_num=1,
        validate_min=True
    )

    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        formset = ProductoFormSet(request.POST, prefix='productos')

        if form.is_valid():
            try:
                with transaction.atomic():
                    proveedor = form.save()
                    formset.instance = proveedor
                    
                    if formset.is_valid():
                        formset.save()
                        messages.success(request, 'Proveedor creado exitosamente')
                        return redirect('compras:lista_proveedores')
                    else:
                        raise ValueError("Error en el formulario de productos")

            except Exception as e:
                messages.error(request, f'Error al crear el proveedor: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        form = ProveedorForm()
        formset = ProductoFormSet(prefix='productos')

    context = {
        'form': form,
        'productos_form': formset,
        'tipos_proveedor': TipoProveedor.objects.filter(activo=True)
    }
    return render(request, 'compras/crear_proveedor.html', context)

@login_required
def lista_proveedores(request):
    query = request.GET.get('q', '')
    tipo = request.GET.get('tipo', '')
    
    proveedores = Proveedor.objects.filter(activo=True)
    
    if query:
        proveedores = proveedores.filter(
            Q(nombre__icontains=query) |
            Q(rut__icontains=query)
        )
    
    if tipo:
        proveedores = proveedores.filter(tipo_proveedor_id=tipo)
    
    context = {
        'proveedores': proveedores,
        'tipos_proveedor': TipoProveedor.objects.filter(activo=True),
        'query': query,
        'tipo_seleccionado': tipo
    }
    return render(request, 'compras/lista_proveedores.html', context)

@login_required
def detalle_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    productos = proveedor.proveedorproducto_set.all()
    ordenes = proveedor.ordenes_compra.all()[:5]
    
    if proveedor.tipo_proveedor.es_materia_prima:
        historial = proveedor.historial_calibres.all()[:5]
    else:
        historial = None
    
    context = {
        'proveedor': proveedor,
        'productos': productos,
        'ordenes': ordenes,
        'historial': historial
    }
    return render(request, 'compras/detalle_proveedor.html', context)

@login_required
def editar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado exitosamente')
            return redirect('compras:detalle_proveedor', pk=pk)
    else:
        form = ProveedorForm(instance=proveedor)
    
    return render(request, 'compras/editar_proveedor.html', {
        'form': form,
        'proveedor': proveedor
    })


@login_required
def lista_proveedores(request):
    """
    Vista para listar todos los proveedores.
    """
    proveedores = Proveedor.objects.all().order_by('nombre')
    
    context = {
        'proveedores': proveedores,
    }
    
    return render(request, 'compras/lista_proveedores.html', context)

# Función auxiliar para validar si un proveedor puede ser eliminado
def puede_eliminar_proveedor(proveedor):
    """
    Verifica si un proveedor puede ser eliminado de forma segura.
    Retorna (bool, str) donde bool indica si se puede eliminar y str contiene el mensaje de error si aplica.
    """
    # Verificar si tiene órdenes de compra asociadas
    if proveedor.ordenescompra.exists():
        return False, "No se puede eliminar el proveedor porque tiene órdenes de compra asociadas."
    
    # Verificar si es proveedor principal de algún producto
    productos_principales = ProveedorProducto.objects.filter(
        proveedor=proveedor,
        es_proveedor_principal=True
    )
    
    if productos_principales.exists():
        return False, "No se puede eliminar el proveedor porque es proveedor principal de algunos productos."
    
    return True, ""

@login_required
def eliminar_proveedor(request, pk):
    """
    Vista para eliminar un proveedor y todos sus productos asociados.
    """
    proveedor = get_object_or_404(Proveedor, pk=pk)
    
    try:
        nombre_proveedor = proveedor.nombre
        
        # Eliminar el proveedor (esto también eliminará los productos asociados por CASCADE)
        proveedor.delete()
        
        messages.success(request, f'Proveedor "{nombre_proveedor}" eliminado exitosamente.')
    except Exception as e:
        messages.error(request, f'Error al eliminar el proveedor: {str(e)}')
    
    return redirect('compras:lista_proveedores')

@login_required
def crear_orden(request):
    DetalleOrdenFormSet = inlineformset_factory(
        OrdenCompra,
        DetalleOrdenCompra,
        form=DetalleOrdenCompraForm,
        extra=0,
        can_delete=True,
        min_num=1,
        validate_min=True,
        fields=['producto', 'cantidad', 'precio_unitario', 'notas']
    )

    if request.method == 'POST':
        form = OrdenCompraForm(request.POST)
        formset = DetalleOrdenFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Generar número de orden
                    año_actual = date.today().year
                    ultimo_numero = OrdenCompra.objects.filter(
                        numero_orden__startswith=f'OC-{año_actual}'
                    ).aggregate(
                        Max('numero_orden')
                    )['numero_orden__max']

                    if ultimo_numero:
                        ultimo_numero = int(ultimo_numero.split('-')[-1])
                        nuevo_numero = ultimo_numero + 1
                    else:
                        nuevo_numero = 1

                    # Crear y guardar la orden
                    orden = form.save(commit=False)
                    orden.numero_orden = f'OC-{año_actual}-{nuevo_numero:04d}'
                    orden.creado_por = request.user
                    orden.subtotal = Decimal('0.00')
                    orden.impuestos = Decimal('0.00')
                    orden.total = Decimal('0.00')
                    orden.save()

                    # Procesar cada detalle válido
                    subtotal_orden = Decimal('0.00')
                    for form_detalle in formset:
                        if form_detalle.cleaned_data and not form_detalle.cleaned_data.get('DELETE'):
                            detalle = form_detalle.save(commit=False)
                            detalle.orden_compra = orden
                            
                            cantidad = form_detalle.cleaned_data.get('cantidad', Decimal('0.00'))
                            precio_unitario = form_detalle.cleaned_data.get('precio_unitario', Decimal('0.00'))
                            
                            detalle.cantidad = cantidad
                            detalle.precio_unitario = precio_unitario
                            detalle.subtotal = cantidad * precio_unitario
                            
                            detalle.save()
                            subtotal_orden += detalle.subtotal

                    # Actualizar totales de la orden
                    orden.subtotal = subtotal_orden
                    orden.impuestos = subtotal_orden * Decimal('0.19')
                    orden.total = orden.subtotal + orden.impuestos
                    orden.save()

                    messages.success(request, 'Orden de compra creada exitosamente')
                    return redirect('compras:lista_ordenes')
            except Exception as e:
                messages.error(request, f'Error al crear la orden: {str(e)}')
        else:
            if formset.errors:
                messages.error(request, 'Por favor verifique los datos de los productos')
            if form.errors:
                messages.error(request, 'Por favor verifique los datos de la orden')
    else:
        form = OrdenCompraForm()
        formset = DetalleOrdenFormSet()

    return render(request, 'compras/crear_orden.html', {
        'form': form,
        'detalles_formset': formset
    })

@login_required
def lista_ordenes(request):
    estado = request.GET.get('estado', '')
    proveedor = request.GET.get('proveedor', '')
    
    ordenes = OrdenCompra.objects.all()
    
    if estado:
        ordenes = ordenes.filter(estado=estado)
    if proveedor:
        ordenes = ordenes.filter(proveedor_id=proveedor)
    
    context = {
        'ordenes': ordenes,
        'estados': OrdenCompra.ESTADO_CHOICES,
        'proveedores': Proveedor.objects.filter(activo=True),
        'estado_seleccionado': estado,
        'proveedor_seleccionado': proveedor
    }
    return render(request, 'compras/lista_ordenes.html', context)

@login_required
def detalle_orden(request, pk):
    orden = get_object_or_404(OrdenCompra, pk=pk)
    detalles = orden.detalles.all()
    
    context = {
        'orden': orden,
        'detalles': detalles
    }
    return render(request, 'compras/detalle_orden.html', context)

    puede_cancelar = orden.estado not in ['RECIBIDA', 'CANCELADA']
    
    context = {
        'orden': orden,
        'detalles': detalles,
        'puede_cancelar': puede_cancelar
    }
    return render(request, 'compras/detalle_orden.html', context)


@login_required
def lista_tipos_proveedor(request):
    tipos = TipoProveedor.objects.all()
    context = {
        'tipos': tipos
    }
    return render(request, 'compras/tipos_proveedor/lista.html', context)

@login_required
def crear_tipo_proveedor(request):
    if request.method == 'POST':
        form = TipoProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de proveedor creado exitosamente')
            return redirect('compras:lista_tipos_proveedor')
    else:
        form = TipoProveedorForm()
    
    return render(request, 'compras/tipos_proveedor/crear.html', {
        'form': form
    })

@login_required
def editar_tipo_proveedor(request, pk):
    tipo = get_object_or_404(TipoProveedor, pk=pk)
    
    if request.method == 'POST':
        form = TipoProveedorForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de proveedor actualizado exitosamente')
            return redirect('compras:lista_tipos_proveedor')
    else:
        form = TipoProveedorForm(instance=tipo)
    
    return render(request, 'compras/tipos_proveedor/editar.html', {
        'form': form,
        'tipo': tipo
    })



@login_required
def editar_orden(request, pk):
    orden = get_object_or_404(OrdenCompra, pk=pk)
    if orden.estado != 'BORRADOR':
        messages.error(request, 'Solo se pueden editar órdenes en estado borrador')
        return redirect('compras:detalle_orden', pk=pk)
    
    DetalleOrdenFormSet = inlineformset_factory(
        OrdenCompra,
        DetalleOrdenCompra,
        form=DetalleOrdenCompraForm,
        extra=1,
        can_delete=True,
        min_num=1,
        validate_min=True,
        fields=['producto', 'cantidad', 'precio_unitario', 'notas']
    )

    if request.method == 'POST':
        form = OrdenCompraForm(request.POST, instance=orden)
        formset = DetalleOrdenFormSet(request.POST, instance=orden)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Guardar la orden
                    orden = form.save(commit=False)
                    
                    # Procesar cada detalle válido
                    subtotal_orden = Decimal('0.00')
                    for form_detalle in formset:
                        if form_detalle.cleaned_data and not form_detalle.cleaned_data.get('DELETE'):
                            detalle = form_detalle.save(commit=False)
                            detalle.orden_compra = orden
                            
                            cantidad = form_detalle.cleaned_data.get('cantidad', Decimal('0.00'))
                            precio_unitario = form_detalle.cleaned_data.get('precio_unitario', Decimal('0.00'))
                            
                            detalle.cantidad = cantidad
                            detalle.precio_unitario = precio_unitario
                            detalle.subtotal = cantidad * precio_unitario
                            
                            detalle.save()
                            subtotal_orden += detalle.subtotal

                    # Actualizar totales de la orden
                    orden.subtotal = subtotal_orden
                    orden.impuestos = subtotal_orden * Decimal('0.19')
                    orden.total = orden.subtotal + orden.impuestos
                    orden.save()
                    
                    # Guardar el formset después de actualizar la orden
                    formset.save()

                    messages.success(request, 'Orden de compra actualizada exitosamente')
                    return redirect('compras:detalle_orden', pk=pk)
            except Exception as e:
                messages.error(request, f'Error al actualizar la orden: {str(e)}')
        else:
            if formset.errors:
                messages.error(request, 'Por favor verifique los datos de los productos')
            if form.errors:
                messages.error(request, 'Por favor verifique los datos de la orden')
    else:
        form = OrdenCompraForm(instance=orden)
        formset = DetalleOrdenFormSet(instance=orden)

    return render(request, 'compras/editar_orden.html', {
        'form': form,
        'detalles_formset': formset,
        'orden': orden
    })

@login_required
def actualizar_estado_orden(request, pk):
    if request.method == 'POST':
        orden = get_object_or_404(OrdenCompra, pk=pk)
        nuevo_estado = request.POST.get('estado')
        
        try:
            with transaction.atomic():
                # Si el nuevo estado es RECIBIDA, usar el método especial
                if nuevo_estado == 'RECIBIDA':

                    try:
                        # Asegurarse de que el usuario esté disponible para el método recibir_orden
                        orden.recibir_orden(request.user)
                        messages.success(request, 'Orden recibida y productos agregados al inventario exitosamente')
                    except ValueError as e:
                        messages.error(request, str(e))
                        return redirect('compras:detalle_orden', pk=pk)
                    
                    if orden.estado != 'CONFIRMADA':
                        messages.error(request, "Solo se pueden recibir órdenes confirmadas")
                        return redirect('compras:detalle_orden', pk=pk)
                    
                    try:
                        # Usar el método recibir_orden del modelo
                        orden.recibir_orden(request.user)
                        messages.success(request, 'Orden recibida y productos agregados al inventario exitosamente')
                    except ValueError as e:
                        messages.error(request, str(e))
                        return redirect('compras:detalle_orden', pk=pk)
                
                # Para otros estados, validar que la transición sea válida
                elif nuevo_estado in dict(OrdenCompra.ESTADO_CHOICES):
                    # Validar transiciones de estado
                    if nuevo_estado == 'CANCELADA' and orden.estado == 'RECIBIDA':
                        messages.error(request, "No se puede cancelar una orden ya recibida")
                        return redirect('compras:detalle_orden', pk=pk)
                    
                    # Si todas las validaciones pasan, actualizar el estado
                    orden.estado = nuevo_estado
                    orden.save()
                    messages.success(request, f'Estado de la orden actualizado a {orden.get_estado_display()}')
                else:
                    messages.error(request, 'Estado no válido')
        
        except Exception as e:
            messages.error(request, f'Error al actualizar el estado: {str(e)}')
            
        return redirect('compras:detalle_orden', pk=pk)
    
    return redirect('compras:lista_ordenes')


@login_required
def agregar_detalle_orden(request, orden_pk):
    orden = get_object_or_404(OrdenCompra, pk=orden_pk)
    if request.method == 'POST':
        form = DetalleOrdenCompraForm(request.POST)
        if form.is_valid():
            detalle = form.save(commit=False)
            detalle.orden_compra = orden
            detalle.save()
            messages.success(request, 'Producto agregado a la orden exitosamente')
            return redirect('compras:detalle_orden', pk=orden_pk)
    else:
        form = DetalleOrdenCompraForm()
    
    context = {
        'form': form,
        'orden': orden
    }
    return render(request, 'compras/ordenes/agregar_detalle.html', context)

@login_required
def eliminar_detalle_orden(request, pk):
    detalle = get_object_or_404(DetalleOrdenCompra, pk=pk)
    orden_pk = detalle.orden_compra.pk
    if request.method == 'POST':
        detalle.delete()
        messages.success(request, 'Producto eliminado de la orden exitosamente')
        return redirect('compras:detalle_orden', pk=orden_pk)
    return redirect('compras:detalle_orden', pk=orden_pk)
