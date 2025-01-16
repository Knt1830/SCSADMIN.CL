# inventario/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MovimientoInventario

@receiver(post_save, sender=MovimientoInventario)
def verificar_stock_minimo(sender, instance, created, **kwargs):
    if created:
        producto = instance.producto
        if producto.verificar_stock_minimo():
            # Aquí puedes añadir lógica para notificar sobre bajo stock
            pass