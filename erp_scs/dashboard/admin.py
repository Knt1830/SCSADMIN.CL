from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'es_admin')
    fieldsets = UserAdmin.fieldsets + (
        ('Permisos Adicionales', {'fields': ('modulos_acceso', 'es_admin')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Permisos Adicionales', {'fields': ('modulos_acceso', 'es_admin')}),
    )

admin.site.register(Usuario, CustomUserAdmin)
