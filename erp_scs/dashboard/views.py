# dashboard/views.py
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Usuario
from django.contrib.auth import update_session_auth_hash

def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            error = "Usuario o contraseña incorrectos"
    return render(request, 'login.html', {'error': error})

def dashboard_view(request):
    # Obtenemos la lista de módulos disponibles
   modulos_disponibles = []
   for modulo_code in request.user.modulos_acceso:
        if modulo_code == 'inventario':
            modulos_disponibles.append({
                'code': 'inventario',
                'name': 'Inventario'
            })
        if modulo_code == 'compras':
            modulos_disponibles.append({
                'code': 'compras',
                'name': 'Compras'
            })
        if modulo_code == 'produccion':
            modulos_disponibles.append({
                'code': 'produccion',
                'name': 'Produccion'
            })
        if modulo_code == 'transporte':
            modulos_disponibles.append({
                'code': 'transporte',
                'name': 'Transporte'
            })
        if modulo_code == 'ventas':
            modulos_disponibles.append({
                'code': 'ventas',
                'name': 'Ventas'
            })
        if modulo_code == 'rrhh':
            modulos_disponibles.append({
                'code': 'rrhh',
                'name': 'RRHH'
            })
   context = {
        'modulos': modulos_disponibles,
        'user': request.user
    }
   return render(request, 'dashboard.html', context)
@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def crear_usuario(request):
    if not request.user.es_admin and not request.user.is_superuser:
        return redirect('dashboard')
    
    context = {
        'modulos_choices': Usuario.MODULOS_CHOICES
    }
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            username = request.POST.get('username')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            modulos = request.POST.getlist('modulos')
            es_admin = request.POST.get('es_admin') == 'on'
            
            # Validaciones básicas
            if not username or not password:
                raise ValueError("Usuario y contraseña son obligatorios")
            
            if not modulos:
                raise ValueError("Debe seleccionar al menos un módulo")
            
            # Crear el usuario
            usuario = Usuario.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email,
                es_admin=es_admin,
                modulos_acceso=modulos
            )
            
            context['success'] = f"Usuario {username} creado exitosamente"
            
        except Exception as e:
            context['error'] = str(e)
    
    return render(request, 'crear_usuario.html', context)
    
@login_required(login_url='login')
def perfil_view(request):
    # Obtener los nombres de los módulos asignados
    modulos_usuario = []
    for modulo_code in request.user.modulos_acceso:
        for code, name in Usuario.MODULOS_CHOICES:
            if code == modulo_code:
                modulos_usuario.append(name)
                break
    
    context = {
        'modulos_usuario': modulos_usuario
    }
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if not request.user.check_password(current_password):
            context['error'] = 'La contraseña actual es incorrecta'
        elif new_password1 != new_password2:
            context['error'] = 'Las nuevas contraseñas no coinciden'
        elif len(new_password1) < 8:
            context['error'] = 'La nueva contraseña debe tener al menos 8 caracteres'
        else:
            request.user.set_password(new_password1)
            request.user.save()
            update_session_auth_hash(request, request.user)  # Mantiene la sesión activa
            context['success'] = 'Contraseña actualizada exitosamente'
    
    return render(request, 'perfil.html', context)