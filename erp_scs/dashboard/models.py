# dashboard/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    MODULOS_CHOICES = [
        ('compras', 'Compras'),
        ('produccion', 'Producción'),
        ('inventario', 'Inventario'),
        ('transporte', 'Transporte'),
        ('ventas', 'Ventas'),
        ('rrhh', 'RRHH'),
        ('finanzas', 'Finanzas'),
    ]
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='usuario_set',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='usuario_set',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
    )
    
    modulos_acceso = models.JSONField(
        default=list,
        help_text='Lista de módulos a los que el usuario tiene acceso'
    )
    es_admin = models.BooleanField(
        default=False,
        verbose_name='Es Administrador'
    )

    def save(self, *args, **kwargs):
        # Si es superuser, asignar todos los módulos y hacer admin
        if self.is_superuser:
            self.es_admin = True
            self.modulos_acceso = [modulo[0] for modulo in self.MODULOS_CHOICES]
        super().save(*args, **kwargs)