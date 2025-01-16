from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from inventario.models import MovimientoInventario



class Lote(models.Model):
    ESTADO_CHOICES = [
        ('PEN', 'Pendiente'),
        ('ACT', 'Activo'),
        ('FIN', 'Finalizado'),
        ('CAN', 'Cancelado')
    ]
    
    # Relaciones
    orden_compra = models.ForeignKey(
        'compras.OrdenCompra',
        on_delete=models.PROTECT,
        related_name='lotes'
    )
    
    # Campos base
    codigo = models.CharField(
        max_length=30,
        unique=True,
        help_text="Código único del lote (ej: LOT-2024-001)"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )
    fecha_inicio = models.DateTimeField(
        null=True,
        blank=True
    )
    fecha_fin = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Control de estado
    estado = models.CharField(
        max_length=3,
        choices=ESTADO_CHOICES,
        default='PEN'
    )
    
    # Trazabilidad
    
    
    modificado_en = models.DateTimeField(
        auto_now=True
    )
    observaciones = models.TextField(
        blank=True
    )

    class Meta:
        ordering = ['-fecha_creacion']
        
    def clean(self):
        if self.fecha_fin and self.fecha_inicio:
            if self.fecha_fin < self.fecha_inicio:
                raise ValidationError('La fecha de fin no puede ser anterior a la fecha de inicio')
    def clean(self):
        if self.fecha_fin and self.fecha_inicio:
            if self.fecha_fin < self.fecha_inicio:
                raise ValidationError('La fecha de fin no puede ser anterior a la fecha de inicio')
        
        # Validar que la orden de compra esté en estado RECIBIDA
        if self.orden_compra and self.orden_compra.estado != 'RECIBIDA':
            raise ValidationError({
                'orden_compra': 'Solo se pueden crear lotes a partir de órdenes de compra en estado RECIBIDA'
            })

class ProduccionDiaria(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente de Procesar'),
        ('EN_PROCESO', 'En Proceso'),
        ('COMPLETADO', 'Producción Completada'),
        ('ANULADO', 'Producción Anulada')
    ]
    
    # Campos existentes
    lote = models.ForeignKey(
        'Lote',
        on_delete=models.PROTECT,
        related_name='producciones'
    )
    trabajador = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='producciones_realizadas',
        null=True,
        blank=True,
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField(
        null=True, 
        blank=True
    )
    merma_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        null=True,
        blank=True
    )
    observaciones = models.TextField(
        blank=True
    )
    
    # Nuevos campos
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE'
    )
    inventario_actualizado = models.BooleanField(
        default=False,
        help_text="Indica si los movimientos de inventario ya fueron procesados"
    )
    fecha_actualizacion_inventario = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ['lote', 'fecha', 'trabajador', 'hora_inicio']
        ordering = ['-fecha', '-hora_inicio']

    def validar_stock_materias_primas(self):
        """
        Valida que haya suficiente stock de todas las materias primas necesarias
        para la producción.
        """
        materias_primas = self.materias_primas.all()
        errores = []
        
        for materia in materias_primas:
            try:
                materia.producto.validar_stock(materia.cantidad)
            except ValidationError as e:
                errores.append(f"Error en {materia.producto.nombre}: {str(e)}")
        
        if errores:
            raise ValidationError(" ".join(errores))
        return True

    def procesar_inventario(self):
        """
        Procesa todos los movimientos de inventario relacionados con esta producción.
        Debe ejecutarse dentro de una transacción.
        """
        if self.inventario_actualizado:
            raise ValidationError("El inventario ya fue actualizado para esta producción")
            
        try:
            # 1. Validar stock disponible
            self.validar_stock_materias_primas()
            
            # 2. Registrar salidas de materias primas
            for materia in self.materias_primas.all():
                MovimientoInventario.objects.create(
                    producto=materia.producto,
                    tipo_movimiento='SALIDA',
                    cantidad=materia.cantidad,
                    descripcion=f"Salida por producción #{self.id}",
                    usuario=self.trabajador,
                    stock_anterior=materia.producto.stock_actual,
                    stock_resultante=materia.producto.stock_actual - materia.cantidad
                )
                materia.producto.ajustar_stock(materia.cantidad, 'SALIDA')
            
            # 3. Registrar entradas de productos terminados
            for item in self.items.all():
                MovimientoInventario.objects.create(
                    producto=item.producto,
                    tipo_movimiento='ENTRADA',
                    cantidad=item.cantidad_producida,
                    descripcion=f"Entrada por producción #{self.id}",
                    usuario=self.trabajador,
                    stock_anterior=item.producto.stock_actual,
                    stock_resultante=item.producto.stock_actual + item.cantidad_producida
                )
                item.producto.ajustar_stock(item.cantidad_producida, 'ENTRADA')
            
            # 4. Actualizar estado
            self.inventario_actualizado = True
            self.fecha_actualizacion_inventario = timezone.now()
            self.estado = 'COMPLETADO'
            self.save()
            
        except Exception as e:
            raise ValidationError(f"Error al procesar el inventario: {str(e)}")

    def anular_produccion(self):
        """
        Anula la producción y revierte los movimientos de inventario si es necesario
        """
        if self.estado == 'ANULADO':
            raise ValidationError("La producción ya está anulada")
            
        if self.inventario_actualizado:
            # Revertir movimientos si el inventario fue actualizado
            try:
                # Revertir salidas (entradas de materias primas)
                for materia in self.materias_primas.all():
                    MovimientoInventario.objects.create(
                        producto=materia.producto,
                        tipo_movimiento='ENTRADA',
                        cantidad=materia.cantidad,
                        descripcion=f"Reversión por anulación de producción #{self.id}",
                        usuario=self.trabajador,
                        stock_anterior=materia.producto.stock_actual,
                        stock_resultante=materia.producto.stock_actual + materia.cantidad
                    )
                    materia.producto.ajustar_stock(materia.cantidad, 'ENTRADA')
                
                # Revertir entradas (salidas de productos terminados)
                for item in self.items.all():
                    MovimientoInventario.objects.create(
                        producto=item.producto,
                        tipo_movimiento='SALIDA',
                        cantidad=item.cantidad_producida,
                        descripcion=f"Reversión por anulación de producción #{self.id}",
                        usuario=self.trabajador,
                        stock_anterior=item.producto.stock_actual,
                        stock_resultante=item.producto.stock_actual - item.cantidad_producida
                    )
                    item.producto.ajustar_stock(item.cantidad_producida, 'SALIDA')
            
            except Exception as e:
                raise ValidationError(f"Error al revertir movimientos de inventario: {str(e)}")
        
        self.estado = 'ANULADO'
        self.save()

class ItemProduccion(models.Model):
    produccion = models.ForeignKey(
        ProduccionDiaria,
        on_delete=models.PROTECT,
        related_name='items'
    )
    producto = models.ForeignKey(
        'inventario.Producto',
        on_delete=models.PROTECT,
        related_name='producciones'
    )
    cantidad_producida = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unidad = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Precio acordado por unidad para este trabajador",
        default=0.00
    )
    calidad = models.CharField(
        max_length=20,
        choices=[
            ('PRIMERA', 'Primera'),
            ('SEGUNDA', 'Segunda'),
            ('TERCERA', 'Tercera')
        ]
    )
class MateriaPrimaUtilizada(models.Model):
    produccion = models.ForeignKey(
        'ProduccionDiaria',
        on_delete=models.PROTECT,
        related_name='materias_primas'
    )
    producto = models.ForeignKey(
        'inventario.Producto',
        on_delete=models.PROTECT,
        limit_choices_to={'tipo_producto': 'MATERIA'},
        related_name='usado_en_producciones'
    )
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    class Meta:
        verbose_name = "Materia Prima Utilizada"
        verbose_name_plural = "Materias Primas Utilizadas"
        unique_together = ['produccion', 'producto']

    def clean(self):
        if self.producto.tipo_producto != 'MATERIA':
            raise ValidationError("El producto debe ser una materia prima")
        
        try:
            self.producto.validar_stock(self.cantidad)
        except ValidationError as e:
            raise ValidationError(f"Error de stock: {str(e)}")

    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad} {self.producto.unidad_medida}"
