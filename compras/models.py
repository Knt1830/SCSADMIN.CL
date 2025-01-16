# compras/models.py
from django.db import models
from inventario.models import Producto
from django.core.validators import RegexValidator
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from datetime import datetime, date
from django.db import transaction
from django.db.models import F
from inventario.models import Producto, MovimientoInventario

class TipoProveedor(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    es_materia_prima = models.BooleanField(
        default=False,
        help_text="Indica si este tipo de proveedor suministra materia prima"
    )
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Tipo de Proveedor"
        verbose_name_plural = "Tipos de Proveedores"

class Proveedor(models.Model):
    # Validador para RUT chileno (XX.XXX.XXX-X)
    rut_validator = RegexValidator(
        regex=r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$',
        message="RUT debe tener formato XX.XXX.XXX-X"
    )
    
    nombre = models.CharField(max_length=200)
    rut = models.CharField(
        max_length=12,
        validators=[rut_validator],
        unique=True,
        verbose_name="RUT"
    )
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    tipo_proveedor = models.ForeignKey(
        TipoProveedor,
        on_delete=models.PROTECT,
        related_name='proveedores'
    )
    productos_suministrados = models.ManyToManyField(
        Producto,
        through='ProveedorProducto',
        related_name='proveedores'
    )
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.rut})"
    
    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']

class ProveedorProducto(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    producto = models.ForeignKey('inventario.Producto', on_delete=models.CASCADE)  # Referencia corregida
    precio_referencia = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    es_proveedor_principal = models.BooleanField(default=False)
    notas = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['proveedor', 'producto']
        verbose_name = "Producto de Proveedor"
        verbose_name_plural = "Productos de Proveedores"

class HistorialCalibre(models.Model):
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        related_name='historial_calibres'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='historial_calibres'
    )
    fecha_entrega = models.DateField()
    calibre = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    calidad = models.CharField(
        max_length=20,
        choices=[
            ('EXCELENTE', 'Excelente'),
            ('BUENA', 'Buena'),
            ('REGULAR', 'Regular'),
            ('DEFICIENTE', 'Deficiente')
        ]
    )
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Historial de Calibre"
        verbose_name_plural = "Historial de Calibres"
        ordering = ['-fecha_entrega']

class OrdenCompra(models.Model):
    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('ENVIADA', 'Enviada'),
        ('CONFIRMADA', 'Confirmada'),
        ('RECIBIDA', 'Recibida'),
        ('CANCELADA', 'Cancelada')
    ]

    @property
    def tiene_lote(self):
        return self.lotes.exists()
    
    
    
    numero_orden = models.CharField(
        max_length=20, 
        unique=True,
        help_text="Formato: OC-YYYY-NNNN"
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name='ordenes_compra'
    )
    fecha_emision = models.DateField()
    fecha_entrega_esperada = models.DateField()
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='BORRADOR'
    )
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    impuestos = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    total = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    notas = models.TextField(blank=True)
    creado_por = models.ForeignKey(
        'dashboard.Usuario',
        on_delete=models.PROTECT,
        related_name='ordenes_compra_creadas'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"OC-{self.numero_orden} - {self.proveedor.nombre}"
    
    class Meta:
        verbose_name = "Orden de Compra"
        verbose_name_plural = "Órdenes de Compra"
        ordering = ['-fecha_emision']

    def recibir_orden(self, usuario):
        from inventario.models import MovimientoInventario
        
        if self.estado != 'CONFIRMADA':
            raise ValueError("Solo se pueden recibir órdenes confirmadas")
            
        try:
            with transaction.atomic():
                # Crear movimientos de inventario para cada detalle
                for detalle in self.detalles.all():
                    MovimientoInventario.objects.create(
                        producto=detalle.producto,
                        tipo_movimiento='ENTRADA',
                        cantidad=detalle.cantidad,
                        descripcion=f'Recepción OC #{self.numero_orden}',
                        usuario=usuario
                    )
                    
                    # Actualizar stock del producto
                    producto = detalle.producto
                    producto.stock_actual += detalle.cantidad
                    producto.save()
                
                # Actualizar estado de la orden
                self.estado = 'RECIBIDA'
                self.save()
                
                return True
                
        except Exception as e:
            raise ValueError(f"Error al recibir la orden: {str(e)}")

class DetalleOrdenCompra(models.Model):
    orden_compra = models.ForeignKey(
        OrdenCompra,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    producto = models.ForeignKey(
        'inventario.Producto',
        on_delete=models.PROTECT
    )
    cantidad = models.DecimalField(
        max_digits=10, 
        decimal_places=2
    )
    precio_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2
    )
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0
    )
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"{self.orden_compra.numero_orden} - {self.producto.nombre}"

    class Meta:
        verbose_name = "Detalle de Orden de Compra"
        verbose_name_plural = "Detalles de Orden de Compra"


    


