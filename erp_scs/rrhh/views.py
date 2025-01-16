from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta, datetime
from .models import Trabajador, PagoMensual, PagoTemporal, ProduccionTemporal
from .forms import TrabajadorForm, PagoMensualForm, ProduccionTemporalForm
import json


@login_required
@permission_required('rrhh.view_trabajador', raise_exception=True)
def home(request):
    # Obtener conteo de trabajadores por categoría
    categorias = [
        {'nombre': 'Planta', 'code': 'PL'},
        {'nombre': 'Conductor', 'code': 'CO'},
        {'nombre': 'Carguero', 'code': 'CA'},
        {'nombre': 'Temporal', 'code': 'TE'},
    ]
    
    for categoria in categorias:
        categoria['total'] = Trabajador.objects.filter(
            categoria=categoria['code']
        ).count()

    # Obtener pagos pendientes
    pagos_mensuales_pendientes = PagoMensual.objects.filter(
        estado='PE'
    ).count()

    pagos_temporales_pendientes = PagoTemporal.objects.filter(
        estado='PE'
    ).count()

    # Calcular producción de la semana actual
    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)

    produccion_semanal = {
        'total_unidades': ProduccionTemporal.objects.filter(
            fecha__range=[inicio_semana, fin_semana]
        ).aggregate(total=Count('cantidad'))['total'] or 0
    }

    context = {
        'categorias': categorias,
        'pagos_mensuales_pendientes': pagos_mensuales_pendientes,
        'pagos_temporales_pendientes': pagos_temporales_pendientes,
        'produccion_semanal': produccion_semanal,
    }

    return render(request, 'rrhh/home.html', context)

@login_required
@permission_required('rrhh.view_trabajador')
def trabajadores(request):
    query = request.GET.get('q', '')
    categoria = request.GET.get('categoria', '')
    
    trabajadores = Trabajador.objects.all()
    
    if query:
        trabajadores = trabajadores.filter(
            Q(nombre__icontains=query) | Q(rut__icontains=query)
        )
    
    if categoria:
        trabajadores = trabajadores.filter(categoria=categoria)
    
    categorias = [
        {'code': 'PL', 'nombre': 'Planta'},
        {'code': 'CO', 'nombre': 'Conductor'},
        {'code': 'CA', 'nombre': 'Carguero'},
        {'code': 'TE', 'nombre': 'Temporal'},
    ]
    
    context = {
        'trabajadores': trabajadores,
        'categorias': categorias,
        'query': query,
        'categoria_actual': categoria
    }
    
    return render(request, 'trabajadores_lista.html', context)

@login_required
@permission_required('rrhh.add_trabajador')
def trabajador_crear(request):
    if request.method == 'POST':
        form = TrabajadorForm(request.POST)
        if form.is_valid():
            trabajador = form.save()
            messages.success(request, 'Trabajador creado exitosamente.')
            return redirect('rrhh:trabajador_detalle', pk=trabajador.pk)
    else:
        form = TrabajadorForm()
    
    return render(request, 'rrhh/trabajadores/form.html', {
        'form': form,
        'titulo': 'Crear Trabajador'
    })

@login_required
@permission_required('rrhh.view_trabajador')
def trabajador_detalle(request, pk):
    trabajador = get_object_or_404(Trabajador, pk=pk)
    
    pagos_mensuales = PagoMensual.objects.filter(trabajador=trabajador).order_by('-mes')
    pagos_temporales = PagoTemporal.objects.filter(trabajador=trabajador).order_by('-semana_inicio')
    producciones = ProduccionTemporal.objects.filter(trabajador=trabajador).order_by('-fecha')
    
    context = {
        'trabajador': trabajador,
        'pagos_mensuales': pagos_mensuales,
        'pagos_temporales': pagos_temporales,
        'producciones': producciones
    }
    
    return render(request, 'rrhh/trabajadores/detalle.html', context)

@login_required
@permission_required('rrhh.add_pagomensual')
def pagos_mensuales(request):
    if request.method == 'POST':
        form = PagoMensualForm(request.POST)
        if form.is_valid():
            pago = form.save()
            messages.success(request, 'Pago mensual registrado exitosamente.')
            return redirect('rrhh:pagos_mensuales')
    else:
        form = PagoMensualForm()
    
    pagos = PagoMensual.objects.all().order_by('-mes', 'trabajador__nombre')
    
    context = {
        'form': form,
        'pagos': pagos
    }
    
    return render(request, 'rrhh/pagos/mensuales.html', context)

@login_required
@permission_required('rrhh.view_pagotemporal')
def pagos_temporales(request):
    # Obtener la semana actual
    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    
    # Obtener producciones de la semana
    producciones = ProduccionTemporal.objects.filter(
        fecha__range=[inicio_semana, fin_semana]
    ).select_related('trabajador')
    
    # Agrupar producciones por trabajador
    resumen_trabajadores = {}
    for produccion in producciones:
        if produccion.trabajador_id not in resumen_trabajadores:
            resumen_trabajadores[produccion.trabajador_id] = {
                'trabajador': produccion.trabajador,
                'total_unidades': 0,
                'total_monto': 0
            }
        resumen_trabajadores[produccion.trabajador_id]['total_unidades'] += produccion.cantidad
        resumen_trabajadores[produccion.trabajador_id]['total_monto'] += produccion.total_calculado
    
    context = {
        'inicio_semana': inicio_semana,
        'fin_semana': fin_semana,
        'resumen_trabajadores': resumen_trabajadores.values()
    }
    
    return render(request, 'rrhh/pagos_temporeros.html', context)

@login_required
@permission_required('rrhh.add_producciontemporal')
def produccion_temporal_crear(request):
    if request.method == 'POST':
        form = ProduccionTemporalForm(request.POST)
        if form.is_valid():
            produccion = form.save()
            messages.success(request, 'Producción registrada exitosamente.')
            return redirect('rrhh:pagos_temporales')
    else:
        form = ProduccionTemporalForm()
    
    return render(request, 'rrhh/produccion/form.html', {
        'form': form,
        'titulo': 'Registrar Producción'
    })

@login_required
@permission_required('rrhh.view_trabajador')
def reportes(request):
    # Obtener fechas del request o usar valores por defecto
    fecha_fin = request.GET.get('fecha_fin')
    fecha_inicio = request.GET.get('fecha_inicio')

    if fecha_fin:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    else:
        fecha_fin = timezone.now().date()

    if fecha_inicio:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    else:
        fecha_inicio = fecha_fin - timedelta(days=30)

    # Consulta base para pagos en el período
    q_pagos_mensuales = Q(
        fecha_registro__date__range=[fecha_inicio, fecha_fin]
    )
    q_pagos_temporales = Q(
        semana_inicio__range=[fecha_inicio, fecha_fin]
    )

    # Calcular totales
    total_pagado_mensual = PagoMensual.objects.filter(
        q_pagos_mensuales,
        estado='PA'
    ).aggregate(total=Sum('monto'))['total'] or 0

    total_pagado_temporal = PagoTemporal.objects.filter(
        q_pagos_temporales,
        estado='PA'
    ).aggregate(total=Sum('monto_total'))['total'] or 0

    total_pendiente_mensual = PagoMensual.objects.filter(
        q_pagos_mensuales,
        estado='PE'
    ).aggregate(total=Sum('monto'))['total'] or 0

    total_pendiente_temporal = PagoTemporal.objects.filter(
        q_pagos_temporales,
        estado='PE'
    ).aggregate(total=Sum('monto_total'))['total'] or 0

    # Obtener datos por categoría
    pagos_por_categoria = []
    for categoria, nombre in Trabajador.CATEGORIA_CHOICES:
        trabajadores_categoria = Trabajador.objects.filter(categoria=categoria).count()
        
        if categoria in ['PL', 'CO', 'CA']:  # Categorías con pago mensual
            total_pagado = PagoMensual.objects.filter(
                q_pagos_mensuales,
                trabajador__categoria=categoria,
                estado='PA'
            ).aggregate(
                total=Sum('monto'),
                trabajadores=Count('trabajador', distinct=True)
            )
        else:  # Temporales
            total_pagado = PagoTemporal.objects.filter(
                q_pagos_temporales,
                trabajador__categoria=categoria,
                estado='PA'
            ).aggregate(
                total=Sum('monto_total'),
                trabajadores=Count('trabajador', distinct=True)
            )

        pagos_por_categoria.append({
            'codigo': categoria,
            'nombre': nombre,
            'trabajadores': trabajadores_categoria,
            'total_pagado': total_pagado['total'] or 0,
            'promedio': (total_pagado['total'] or 0) / trabajadores_categoria if trabajadores_categoria > 0 else 0
        })

    # Preparar datos para el gráfico
    datos_grafico = {
        'labels': [cat['nombre'] for cat in pagos_por_categoria],
        'datos': [cat['trabajadores'] for cat in pagos_por_categoria]
    }

    # Calcular totales generales
    totales = {
        'pagado': total_pagado_mensual + total_pagado_temporal,
        'pendiente': total_pendiente_mensual + total_pendiente_temporal,
        'trabajadores': sum(cat['trabajadores'] for cat in pagos_por_categoria),
    }
    
    # Calcular promedio si hay trabajadores
    if totales['trabajadores'] > 0:
        totales['promedio'] = totales['pagado'] / totales['trabajadores']
    else:
        totales['promedio'] = 0

    context = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'totales': totales,
        'pagos_por_categoria': pagos_por_categoria,
        'datos_grafico': json.dumps(datos_grafico),
    }

    return render(request, 'rrhh/reportes/index.html', context)