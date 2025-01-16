# dashboard/context_processors.py
from .models import Usuario

def navigation_modules(request):
    if not request.user.is_authenticated:
        return {'modulos': []}
    
    modulos = []
    for code, name in Usuario.MODULOS_CHOICES:
        # Verificar si el usuario es superusuario o tiene acceso al módulo
        if request.user.is_superuser or code in request.user.modulos_acceso:
            modulos.append({
                'code': code,
                'name': name
            })
    
    return {'modulos': modulos}