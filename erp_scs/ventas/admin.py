# ventas/admin.py
from django.contrib import admin
from .models import Cliente, Venta, DetalleVenta, CreditoCliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'telefono', 'fecha_registro')
    search_fields = ('nombre', 'rut', 'telefono')
    list_filter = ('fecha_registro',)

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha_venta', 'total_venta', 'estado', 'es_credito')
    list_filter = ('estado', 'es_credito', 'fecha_venta')
    search_fields = ('cliente__nombre', 'cliente__rut')

@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'producto_id', 'nombre_producto', 'cantidad', 'precio_unitario', 'subtotal')
    search_fields = ('nombre_producto', 'venta__cliente__nombre')

@admin.register(CreditoCliente)
class CreditoClienteAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'venta', 'monto_total', 'monto_pagado', 'fecha_credito', 'fecha_vencimiento', 'estado')
    list_filter = ('estado', 'fecha_credito', 'fecha_vencimiento')
    search_fields = ('cliente__nombre', 'cliente__rut')
