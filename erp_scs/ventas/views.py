# ventas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
import json
from decimal import Decimal, InvalidOperation
from django.http import HttpResponse, HttpResponseNotAllowed


from inventario.models import Producto, MovimientoInventario
from .models import Cliente, Venta, DetalleVenta, CreditoCliente, PagoCredito
from .forms import ClienteForm, VentaForm, DetalleVentaFormSet

@login_required(login_url='login')
def home_ventas(request):
    """Vista principal del módulo de ventas"""
    context = {
        'total_clientes': Cliente.objects.count(),
        'ventas_mes': Venta.objects.filter(
            fecha_venta__month=timezone.now().month,
            fecha_venta__year=timezone.now().year
        ).count(),
        'creditos_pendientes': CreditoCliente.objects.filter(
            estado__in=['PENDIENTE', 'PARCIAL']
        ).count()
    }
    return render(request, 'ventas/home.html', context)

@login_required(login_url='login')
def registrar_cliente(request):
    """Vista para registrar un nuevo cliente"""
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.usuario_registro = request.user
            cliente.save()
            messages.success(request, f'Cliente {cliente.nombre} registrado exitosamente')
            return redirect('ventas:nueva_venta')
    else:
        form = ClienteForm()
    return render(request, 'ventas/registrar_cliente.html', {'form': form})

@login_required(login_url='login')
def lista_clientes(request):
    """Vista para listar clientes"""
    # Parámetros de búsqueda
    query = request.GET.get('q', '')
    
    clientes = Cliente.objects.all()
    
    if query:
        clientes = clientes.filter(
            Q(nombre__icontains=query) |
            Q(rut__icontains=query) |
            Q(telefono__icontains=query)
        )
    
    context = {
        'clientes': clientes,
        'query': query
    }
    return render(request, 'ventas/lista_clientes.html', context)

@login_required(login_url='login')
def detalle_cliente(request, cliente_id):
    """Vista para mostrar detalles de un cliente"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    # Obtener ventas del cliente
    ventas = cliente.ventas.all().order_by('-fecha_venta')
    
    # Obtener créditos pendientes
    creditos_pendientes = CreditoCliente.objects.filter(
        cliente=cliente, 
        estado__in=['PENDIENTE', 'PARCIAL']
    )
    
    context = {
        'cliente': cliente,
        'ventas': ventas,
        'creditos_pendientes': creditos_pendientes,
        'total_creditos_pendientes': creditos_pendientes.aggregate(
            total=Sum('monto_total')
        )['total'] or 0
    }
    return render(request, 'ventas/detalle_cliente.html', context)

@login_required
def nueva_venta(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Procesar cliente
                if request.POST.get('tipo_cliente') == 'existente':
                    cliente = get_object_or_404(Cliente, id=request.POST.get('cliente'))
                else:
                    # Crear nuevo cliente
                    cliente = Cliente.objects.create(
                        nombre=request.POST.get('nombre_cliente'),
                        rut=request.POST.get('rut_cliente'),
                        telefono=request.POST.get('telefono_cliente'),
                        direccion=request.POST.get('direccion_cliente'),
                        usuario_registro=request.user
                    )

                # Crear la venta
                venta = Venta.objects.create(
                cliente=cliente,
                usuario_venta=request.user,
                es_credito=request.POST.get('es_credito') == 'on',
                dias_credito=None,  # Inicialmente establecemos como None
                observaciones=request.POST.get('observaciones'),
                total_venta=0, # Se actualizará después
                estado='PENDIENTE'
                )

                # Procesar productos
                total_venta = Decimal('0.00')  # Inicializar como Decimal
                productos_json = json.loads(request.POST.get('productos_json', '[]'))

                for producto_data in productos_json:
                    producto = get_object_or_404(Producto, id=producto_data['id'])
                    cantidad = Decimal(str(producto_data['cantidad']))  # Convertir a Decimal
                    precio = Decimal(str(producto_data['precio']))      # Convertir a Decimal

                    # Validar stock
                    if cantidad > producto.stock_actual:
                        raise ValueError(f'Stock insuficiente para {producto.nombre}')

                    # Crear detalle de venta
                    detalle = DetalleVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio,
                        nombre_producto=producto.nombre
                    )
                    total_venta += detalle.subtotal

                    # Actualizar inventario
                    MovimientoInventario.objects.create(
                        producto=producto,
                        tipo_movimiento='SALIDA',
                        cantidad=cantidad,
                        descripcion=f'Venta #{venta.id}',
                        usuario=request.user,
                        stock_anterior=producto.stock_actual,
                        stock_resultante=producto.stock_actual - cantidad
                    )
                    producto.stock_actual -= cantidad
                    producto.save()

                # Procesar envases si están incluidos
                if request.POST.get('incluir_envases') == 'on':
                    envases_json = json.loads(request.POST.get('envases_json', '[]'))
                    
                    for envase_data in envases_json:
                        try:
                            envase = get_object_or_404(Producto, id=envase_data['id'], tipo_producto='ENVASE')
                            # Asegurarse de que los valores son válidos antes de convertir
                            if not envase_data.get('cantidad') or not envase_data.get('precio'):
                                raise ValueError(f'Cantidad y precio son requeridos para el envase {envase.nombre}')
                            
                            # Convertir y validar cantidad
                            try:
                                cantidad = Decimal(str(envase_data['cantidad']))
                                if cantidad <= 0:
                                    raise ValueError(f'La cantidad debe ser mayor a 0 para el envase {envase.nombre}')
                            except (InvalidOperation, ValueError):
                                raise ValueError(f'Cantidad inválida para el envase {envase.nombre}')
                            
                            # Convertir y validar precio
                            try:
                                precio = Decimal(str(envase_data['precio']))
                                if precio < 0:
                                    raise ValueError(f'El precio no puede ser negativo para el envase {envase.nombre}')
                            except (InvalidOperation, ValueError):
                                raise ValueError(f'Precio inválido para el envase {envase.nombre}')

                            # Validar stock
                            if cantidad > envase.stock_actual:
                                raise ValueError(f'Stock insuficiente para el envase {envase.nombre}')

                            # Crear detalle de venta para envase
                            detalle = DetalleVenta.objects.create(
                                venta=venta,
                                producto=envase,
                                cantidad=cantidad,
                                precio_unitario=precio,
                                nombre_producto=envase.nombre
                            )
                            total_venta += detalle.subtotal

                            # Actualizar inventario de envases
                            MovimientoInventario.objects.create(
                                producto=envase,
                                tipo_movimiento='SALIDA',
                                cantidad=cantidad,
                                descripcion=f'Venta #{venta.id} - Envase',
                                usuario=request.user,
                                stock_anterior=envase.stock_actual,
                                stock_resultante=envase.stock_actual - cantidad
                            )
                            envase.stock_actual -= cantidad
                            envase.save()
                        
                        except Exception as e:
                            raise ValueError(f'Error procesando envase: {str(e)}')

                # Actualizar total de la venta
                venta.total_venta = total_venta
                venta.save()

        
                if request.POST.get('es_credito') == 'on':
                    try:
                        # Convertir explícitamente a int y manejar el caso donde no hay valor
                        dias_credito = int(request.POST.get('dias_credito', '30'))
                        venta.dias_credito = dias_credito
                        venta.save()
                        
                        fecha_vencimiento = timezone.now().date() + timedelta(days=dias_credito)
                        
                        # Verificar si ya existe un crédito para esta venta
                        credito, created = CreditoCliente.objects.get_or_create(
                            venta=venta,
                            defaults={
                                'cliente': cliente,
                                'monto_total': total_venta,
                                'fecha_vencimiento': fecha_vencimiento,
                                'estado': 'PENDIENTE'
                            }
                        )
                        
                        # Si el crédito ya existía, actualizamos sus valores
                        if not created:
                            credito.monto_total = total_venta
                            credito.fecha_vencimiento = fecha_vencimiento
                            credito.save()
                        
                        else:
                            venta.estado = 'PAGADA'
                            venta.save()
              
                

                    except ValueError as e:
                        raise ValueError(f'Error en los días de crédito: {str(e)}')

                messages.success(request, 'Venta registrada exitosamente')
                return redirect('ventas:detalle_venta', venta_id=venta.id)

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error al procesar la venta: {str(e)}')

        return render(request, 'ventas/nueva_venta.html', context)

                       

    # Contexto para GET request
    context = {
        'clientes': Cliente.objects.all(),
        'productos_venta': Producto.objects.filter(
            activo=True
        ).select_related('categoria')
    }
    
    return render(request, 'ventas/nueva_venta.html', context)
@login_required
def detalle_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    detalles = venta.detalles.all()
    
    # Separar detalles normales y envases
    detalles_envases = detalles.filter(producto__tipo_producto='ENVASE')
    detalles_productos = detalles.exclude(producto__tipo_producto='ENVASE')
    
    # Calcular subtotales
    subtotal_productos = sum(d.subtotal for d in detalles_productos)
    total_envases = sum(d.subtotal for d in detalles_envases)
    
    # Obtener información de crédito si existe
    credito = CreditoCliente.objects.filter(venta=venta).first()
    
    context = {
        'venta': venta,
        'detalles': detalles_productos,
        'detalles_envases': detalles_envases,
        'subtotal_productos': subtotal_productos,
        'total_envases': total_envases,
        'credito': credito
    }
    return render(request, 'ventas/detalle_venta.html', context)

@login_required(login_url='login')
def lista_ventas(request):
    """Vista para listar ventas"""
    # Parámetros de búsqueda
    cliente_id = request.GET.get('cliente')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    estado = request.GET.get('estado')
    
    ventas = Venta.objects.all().order_by('-fecha_venta')
    
    # Aplicar filtros
    if cliente_id:
        ventas = ventas.filter(cliente_id=cliente_id)
    
    if fecha_desde:
        ventas = ventas.filter(fecha_venta__date__gte=fecha_desde)
    
    if fecha_hasta:
        ventas = ventas.filter(fecha_venta__date__lte=fecha_hasta)
    
    if estado:
        ventas = ventas.filter(estado=estado)
    
    context = {
        'ventas': ventas,
        'clientes': Cliente.objects.all(),
        'estados': Venta.ESTADO_CHOICES
    }
    return render(request, 'ventas/lista_ventas.html', context)

@login_required
def gestionar_creditos(request):
    # Obtener los filtros
    cliente_id = request.GET.get('cliente')
    estado = request.GET.get('estado')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    # Query base
    creditos = CreditoCliente.objects.select_related('cliente', 'venta').filter(
        Q(estado='PENDIENTE') | Q(estado='PARCIAL')
    )
    
    # Aplicar filtros
    if cliente_id:
        creditos = creditos.filter(cliente_id=cliente_id)
    
    if estado:
        creditos = creditos.filter(estado=estado)
    
    if fecha_desde:
        creditos = creditos.filter(fecha_vencimiento__gte=fecha_desde)
    
    if fecha_hasta:
        creditos = creditos.filter(fecha_vencimiento__lte=fecha_hasta)
    
    # Ordenar por fecha de vencimiento
    creditos = creditos.order_by('fecha_vencimiento')
    
    context = {
        'creditos': creditos,
        'clientes': Cliente.objects.all(),
        'today': timezone.now().date(),
        'filtros': {
            'cliente': cliente_id,
            'estado': estado,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta
        }
    }
    
    return render(request, 'ventas/gestionar_creditos.html', context)

@login_required
def registrar_pago_credito(request, credito_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    
    try:
        with transaction.atomic():
            credito = get_object_or_404(CreditoCliente, id=credito_id)
            monto_pago = Decimal(request.POST.get('monto_pago', '0'))
            observaciones = request.POST.get('observaciones', '')

            # Validaciones
            if monto_pago <= 0:
                raise ValueError("El monto del pago debe ser mayor a 0")
            
            if monto_pago > credito.monto_pendiente:
                raise ValueError("El monto del pago no puede ser mayor al saldo pendiente")

            # Registrar el pago
            PagoCredito.objects.create(
                credito=credito,
                monto=monto_pago,
                fecha_pago=timezone.now(),
                observaciones=observaciones,
                usuario=request.user
            )

            # Actualizar el monto pagado del crédito
            credito.monto_pagado += monto_pago
            
            # Actualizar el estado del crédito
            if credito.monto_pagado >= credito.monto_total:
                credito.estado = 'PAGADO'
                # Si el crédito está completamente pagado, actualizar la venta
                credito.venta.estado = 'PAGADA'
                credito.venta.save()
            elif credito.monto_pagado > 0:
                credito.estado = 'PARCIAL'
            
            credito.save()

            messages.success(request, 'Pago registrado exitosamente')

    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f'Error al registrar el pago: {str(e)}')
    
    return redirect('ventas:gestionar_creditos')

@login_required(login_url='login')
def editar_cliente(request, cliente_id):
    """Vista para editar un cliente existente"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cliente {cliente.nombre} actualizado exitosamente')
            return redirect('ventas:detalle_cliente', cliente_id=cliente.id)
    else:
        form = ClienteForm(instance=cliente)
    
    context = {
        'form': form,
        'cliente': cliente
    }
    return render(request, 'ventas/editar_cliente.html', context)

@login_required(login_url='login')
def editar_venta(request, venta_id):
    """Vista para editar una venta existente"""
    venta = get_object_or_404(Venta, id=venta_id)
    
    if request.method == 'POST':
        venta_form = VentaForm(request.POST, instance=venta)
        detalle_venta_formset = DetalleVentaFormSet(request.POST, instance=venta)
        
        if venta_form.is_valid() and detalle_venta_formset.is_valid():
            with transaction.atomic():
                # Revertir movimientos de inventario anteriores
                for detalle in venta.detalles.all():
                    producto = detalle.producto
                    producto.ajustar_stock(detalle.cantidad, 'ENTRADA')
                
                # Guardar venta y detalles
                venta = venta_form.save()
                detalle_venta_formset.save()
                
                # Actualizar stock con los nuevos detalles
                for detalle in detalle_venta_formset.instances:
                    if not detalle.id:  # Nuevo detalle
                        continue
                    producto = detalle.producto
                    producto.ajustar_stock(detalle.cantidad, 'SALIDA')
                
                messages.success(request, 'Venta actualizada exitosamente')
                return redirect('ventas:detalle_venta', venta_id=venta.id)
    else:
        venta_form = VentaForm(instance=venta)
        detalle_venta_formset = DetalleVentaFormSet(instance=venta)
    
    # Obtener productos disponibles para venta
    productos_venta = Producto.objects.filter(
        activo=True, 
        tipo_producto='VENTA'
    )
    
    context = {
        'venta_form': venta_form,
        'detalle_venta_formset': detalle_venta_formset,
        'venta': venta,
        'productos_venta': productos_venta
    }
    return render(request, 'ventas/editar_venta.html', context)
