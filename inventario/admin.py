# inventario/admin.py
from django.contrib import admin
from .models import Categoria, Producto, Lote, MovimientoInventario

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo')
    search_fields = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'tipo_producto', 'stock_actual', 'activo')
    list_filter = ('categoria', 'tipo_producto', 'activo')
    search_fields = ('codigo', 'nombre')

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('numero_lote', 'producto', 'peso_inicial', 'peso_procesado', 'estado')
    list_filter = ('estado',)
    search_fields = ('numero_lote',)

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = (
        'fecha_movimiento',
        'producto',
        'tipo_movimiento',
        'cantidad',
        'stock_anterior',
        'stock_resultante',
        'usuario'
    )
    list_filter = (
        'tipo_movimiento',
        'fecha_movimiento',
        'producto__tipo_producto'
    )
    search_fields = (
        'producto__nombre',
        'producto__codigo',
        'descripcion',
        'documento_referencia'
    )
    readonly_fields = (
        'fecha_movimiento',
        'stock_anterior',
        'stock_resultante'
    )
    date_hierarchy = 'fecha_movimiento'
    ordering = ['-fecha_movimiento']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'producto',
            'usuario'
        )