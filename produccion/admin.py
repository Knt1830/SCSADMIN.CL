from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import Lote, ProduccionDiaria, ItemProduccion
from django.utils import timezone

import datetime

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'orden_compra', 'estado', 'fecha_inicio', 
                   'dias_activo', 'total_producido')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('codigo', 'orden_compra__codigo', 'observaciones')
    readonly_fields = ('fecha_creacion', 'modificado_en')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'orden_compra', 'estado')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Trazabilidad', {
            'fields': ('creado_por', 'fecha_creacion', 'modificado_en', 'observaciones'),
            'classes': ('collapse',)
        }),
    )

    def dias_activo(self, obj):
        if obj.fecha_inicio and not obj.fecha_fin:
            return (timezone.now().date() - obj.fecha_inicio.date()).days
        elif obj.fecha_inicio and obj.fecha_fin:
            return (obj.fecha_fin.date() - obj.fecha_inicio.date()).days
        return 0
    dias_activo.short_description = 'Días Activo'

    def total_producido(self, obj):
        total = ItemProduccion.objects.filter(
            produccion__lote=obj
        ).aggregate(
            total=Sum('cantidad_producida')
        )['total'] or 0
        return format_html('<b>{}</b> unidades', total)
    total_producido.short_description = 'Total Producido'

    actions = ['finalizar_lotes']

    def finalizar_lotes(self, request, queryset):
        updated = queryset.filter(estado='ACT').update(
            estado='FIN',
            fecha_fin=timezone.now()
        )
        self.message_user(request, f'{updated} lotes fueron finalizados.')
    finalizar_lotes.short_description = "Finalizar lotes seleccionados"

@admin.register(ProduccionDiaria)
class ProduccionDiariaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'lote',  'hora_inicio', 
                   'duracion', 'items_producidos')
    list_filter = ('fecha', 'lote__estado')
    search_fields = ('lote__codigo', 'observaciones')
    date_hierarchy = 'fecha'

    def duracion(self, obj):
        if obj.hora_fin:
            inicio = datetime.combine(obj.fecha, obj.hora_inicio)
            fin = datetime.combine(obj.fecha, obj.hora_fin)
            duracion = fin - inicio
            return f"{duracion.seconds // 3600}h {(duracion.seconds // 60) % 60}m"
        return "En proceso"
    duracion.short_description = 'Duración'

    def items_producidos(self, obj):
        return obj.items.count()
    items_producidos.short_description = 'Items Producidos'

@admin.register(ItemProduccion)
class ItemProduccionAdmin(admin.ModelAdmin):
    list_display = ('produccion', 'producto', 'cantidad_producida', 
                   'calidad', 'peso_total')
    list_filter = ('calidad', 'produccion__fecha', 'producto')
    search_fields = ('producto__nombre', 'produccion__lote__codigo')
    
    def peso_total(self, obj):
        peso = obj.cantidad_producida * obj.peso_unidad
        return f"{peso/1000:.2f} kg"
    peso_total.short_description = 'Peso Total'

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return ('produccion', 'producto', 'creado_en', 'modificado_en')
        return ('creado_en', 'modificado_en')

class ItemProduccionInline(admin.TabularInline):
    model = ItemProduccion
    extra = 1
    fields = ('producto', 'cantidad_producida', 'calidad', 'peso_unidad')
    
# Modificar ProduccionDiariaAdmin para incluir el inline
ProduccionDiariaAdmin.inlines = [ItemProduccionInline]
