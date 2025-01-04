from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Sum, Q

from .models import Vehiculo, Chofer, GastoVehiculo
from .forms import VehiculoForm, ChoferForm, GastoVehiculoForm

@login_required
def transporte_home(request):
    """Vista principal del módulo de transporte"""
    # Obtener contadores y datos principales
    vehiculos_totales = Vehiculo.objects.count()
    vehiculos_disponibles = Vehiculo.objects.filter(estado='disponible').count()
    choferes_totales = Chofer.objects.count()
    choferes_con_vehiculo = Chofer.objects.filter(vehiculo_asignado__isnull=False).count()

    context = {
        'vehiculos_totales': vehiculos_totales,
        'vehiculos_disponibles': vehiculos_disponibles,
        'choferes_totales': choferes_totales,
        'choferes_con_vehiculo': choferes_con_vehiculo,
    }
    return render(request, 'transporte/home.html', context)

@login_required
def lista_vehiculos(request):
    """Lista de todos los vehículos"""
    # Filtros y búsqueda
    query = request.GET.get('q', '')
    estado = request.GET.get('estado', '')

    vehiculos = Vehiculo.objects.all()
    
    if query:
        vehiculos = vehiculos.filter(
            Q(modelo__icontains=query) | 
            Q(marca__icontains=query) | 
            Q(patente__icontains=query)
        )
    
    if estado:
        vehiculos = vehiculos.filter(estado=estado)

    # Calcular gastos por vehículo
    for vehiculo in vehiculos:
        vehiculo.total_gastos = GastoVehiculo.objects.filter(vehiculo=vehiculo).aggregate(
            total=Sum('monto')
        )['total'] or 0

    context = {
        'vehiculos': vehiculos,
        'query': query,
        'estado': estado,
    }
    return render(request, 'transporte/lista_vehiculos.html', context)

@login_required
def detalle_vehiculo(request, pk):
    """Detalle de un vehículo específico"""
    vehiculo = get_object_or_404(Vehiculo, pk=pk)
    
    # Obtener gastos del vehículo
    gastos = GastoVehiculo.objects.filter(vehiculo=vehiculo).order_by('-fecha')
    
    # Calcular totales por tipo de gasto
    totales_gastos = gastos.values('tipo').annotate(total=Sum('monto'))
    
    # Verificar si hay un chofer asignado
    chofer_asignado = Chofer.objects.filter(vehiculo_asignado=vehiculo).first()

    context = {
        'vehiculo': vehiculo,
        'gastos': gastos,
        'totales_gastos': totales_gastos,
        'chofer_asignado': chofer_asignado,
    }
    return render(request, 'transporte/detalle_vehiculo.html', context)

@login_required
@permission_required('transporte.add_vehiculo', raise_exception=True)
def crear_vehiculo(request):
    """Crear un nuevo vehículo"""
    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vehículo creado exitosamente.')
            return redirect('transporte:lista_vehiculos')
    else:
        form = VehiculoForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Vehículo',
    }
    return render(request, 'transporte/crear_vehiculo.html', context)

@login_required
@permission_required('transporte.change_vehiculo', raise_exception=True)
def editar_vehiculo(request, pk):
    """Editar un vehículo existente"""
    vehiculo = get_object_or_404(Vehiculo, pk=pk)
    
    if request.method == 'POST':
        form = VehiculoForm(request.POST, instance=vehiculo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vehículo actualizado exitosamente.')
            return redirect('transporte:detalle_vehiculo', pk=vehiculo.pk)
    else:
        form = VehiculoForm(instance=vehiculo)
    
    context = {
        'form': form,
        'vehiculo': vehiculo,
        'titulo': 'Editar Vehículo',
    }
    return render(request, 'transporte/editar_vehiculo.html', context)

@login_required
def lista_choferes(request):
    """Lista de todos los choferes"""
    # Filtros y búsqueda
    query = request.GET.get('q', '')
    choferes = Chofer.objects.all()
    
    if query:
        choferes = choferes.filter(
            Q(nombre__icontains=query) | 
            Q(rut__icontains=query) | 
            Q(telefono__icontains=query)
        )

    # Agregar información de vehículos
    for chofer in choferes:
        chofer.vehiculo = chofer.vehiculo_asignado

    context = {
        'choferes': choferes,
        'query': query,
    }
    return render(request, 'transporte/lista_choferes.html', context)

@login_required
def detalle_chofer(request, pk):
    """Detalle de un chofer específico"""
    chofer = get_object_or_404(Chofer, pk=pk)
    
    context = {
        'chofer': chofer,
    }
    return render(request, 'transporte/detalle_chofer.html', context)

@login_required
@permission_required('transporte.add_chofer', raise_exception=True)
def crear_chofer(request):
    """Crear un nuevo chofer"""
    if request.method == 'POST':
        form = ChoferForm(request.POST)
        if form.is_valid():
            chofer = form.save(commit=False)
            
            # Si se asigna un vehículo, cambiar su estado
            if form.cleaned_data['vehiculo_asignado']:
                vehiculo = form.cleaned_data['vehiculo_asignado']
                vehiculo.estado = 'en_uso'
                vehiculo.save()
            
            chofer.save()
            messages.success(request, 'Chofer creado exitosamente.')
            return redirect('transporte:lista_choferes')
    else:
        form = ChoferForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Chofer',
    }
    return render(request, 'transporte/crear_chofer.html', context)

@login_required
@permission_required('transporte.change_chofer', raise_exception=True)
def editar_chofer(request, pk):
    """Editar un chofer existente"""
    chofer = get_object_or_404(Chofer, pk=pk)
    
    if request.method == 'POST':
        form = ChoferForm(request.POST, instance=chofer)
        if form.is_valid():
            # Manejar cambios de vehículo
            vehiculo_anterior = chofer.vehiculo_asignado
            nuevo_vehiculo = form.cleaned_data['vehiculo_asignado']
            
            # Guardar chofer con nuevo vehículo
            chofer = form.save(commit=False)
            
            # Actualizar estados de vehículos
            if vehiculo_anterior and vehiculo_anterior != nuevo_vehiculo:
                vehiculo_anterior.estado = 'disponible'
                vehiculo_anterior.save()
            
            if nuevo_vehiculo:
                nuevo_vehiculo.estado = 'en_uso'
                nuevo_vehiculo.save()
            
            chofer.save()
            
            messages.success(request, 'Chofer actualizado exitosamente.')
            return redirect('transporte:detalle_chofer', pk=chofer.pk)
    else:
        form = ChoferForm(instance=chofer)
    
    context = {
        'form': form,
        'chofer': chofer,
        'titulo': 'Editar Chofer',
    }
    return render(request, 'transporte/editar_chofer.html', context)

@login_required
def lista_gastos_vehiculo(request):
    """Lista de todos los gastos de vehículos"""
    # Filtros y búsqueda
    query = request.GET.get('q', '')
    tipo = request.GET.get('tipo', '')

    gastos = GastoVehiculo.objects.all().order_by('-fecha')
    
    if query:
        gastos = gastos.filter(
            Q(vehiculo__modelo__icontains=query) | 
            Q(vehiculo__marca__icontains=query) | 
            Q(vehiculo__patente__icontains=query)
        )
    
    if tipo:
        gastos = gastos.filter(tipo=tipo)

    # Calcular totales
    total_gastos = gastos.aggregate(total=Sum('monto'))['total'] or 0

    context = {
        'gastos': gastos,
        'query': query,
        'tipo': tipo,
        'total_gastos': total_gastos,
    }
    return render(request, 'transporte/lista_gasto_vehiculo.html', context)

@login_required
@permission_required('transporte.add_gastovehiculo', raise_exception=True)
def registrar_gasto_vehiculo(request):
    """Registrar un nuevo gasto de vehículo"""
    if request.method == 'POST':
        form = GastoVehiculoForm(request.POST)
        if form.is_valid():
            gasto = form.save()
            messages.success(request, 'Gasto registrado exitosamente.')
            return redirect('transporte:lista_gastos_vehiculo')
    else:
        form = GastoVehiculoForm()
    
    context = {
        'form': form,
        'titulo': 'Registrar Gasto de Vehículo',
    }
    return render(request, 'transporte/registrar_gasto_vehiculo.html', context)

@login_required
def detalle_gasto_vehiculo(request, pk):
    """Detalle de un gasto de vehículo específico"""
    gasto = get_object_or_404(GastoVehiculo, pk=pk)
    
    context = {
        'gasto': gasto,
    }
    return render(request, 'transporte/detalle_gasto_vehiculo.html', context)
