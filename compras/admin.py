# compras/admin.py
from django.contrib import admin
from .models import (
    TipoProveedor, 
    Proveedor, 
    ProveedorProducto,
    OrdenCompra, 
    DetalleOrdenCompra, 
    HistorialCalibre
)

class DetalleOrdenCompraInline(admin.TabularInline):
    model = DetalleOrdenCompra
    extra = 1

@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = ('get_numero_orden', 'proveedor', 'fecha_emision', 'estado', 'total')
    list_filter = ('estado', 'fecha_emision')
    search_fields = ('numero_orden', 'proveedor__nombre')
    date_hierarchy = 'fecha_emision'
    inlines = [DetalleOrdenCompraInline]

    def get_numero_orden(self, obj):
        return obj.numero_orden
    get_numero_orden.short_description = 'Número de Orden'
    get_numero_orden.admin_order_field = 'numero_orden'

@admin.register(TipoProveedor)
class TipoProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'es_materia_prima', 'activo')
    search_fields = ('nombre',)
    list_filter = ('es_materia_prima', 'activo')

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'tipo_proveedor', 'telefono', 'activo')
    search_fields = ('nombre', 'rut')
    list_filter = ('tipo_proveedor', 'activo')
    date_hierarchy = 'fecha_registro'

@admin.register(ProveedorProducto)
class ProveedorProductoAdmin(admin.ModelAdmin):
    list_display = ('proveedor', 'producto', 'precio_referencia', 'es_proveedor_principal')
    search_fields = ('proveedor__nombre', 'producto__nombre')
    list_filter = ('es_proveedor_principal',)

@admin.register(HistorialCalibre)
class HistorialCalibreAdmin(admin.ModelAdmin):
    list_display = ('proveedor', 'producto', 'fecha_entrega', 'calibre', 'calidad')
    search_fields = ('proveedor__nombre', 'producto__nombre', 'calibre')
    list_filter = ('calidad', 'fecha_entrega')
    date_hierarchy = 'fecha_entrega'