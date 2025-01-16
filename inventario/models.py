# inventario/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db.models import F
from decimal import Decimal

class Categoria(models.Model):
    TIPO_CHOICES = [
        ('FRU', 'Frutas'),
        ('ENV', 'Envases'),
        ('MIS', 'Misceláneos')
    ]
    
    nombre = models.CharField(max_length=50)
    tipo = models.CharField(max_length=3, choices=TIPO_CHOICES)
    descripcion = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.nombre}"
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

class Producto(models.Model):
    TIPO_PRODUCTO_CHOICES = [
        ('VENTA', 'Producto para Venta'),
        ('MATERIA', 'Materia Prima'),
        ('ENVASE', 'Envase'),
        ('MISC', 'Misceláneo')
    ]
    
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    TIPO_CHOICES = [
        ('FRU', 'Frutas'),
        ('ENV', 'Envases'),
        ('MIS', 'Misceláneos')
    ]
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT) 
    tipo_producto = models.CharField(max_length=10, choices=TIPO_PRODUCTO_CHOICES)
    UNIDAD_MEDIDA_CHOICES = [
        ("Kg", "Kilogramo"),
        ("Und", "Unidad"),
        ("Gamela", "Gamela"),
    ]
    unidad_medida = models.CharField(max_length=10, choices=UNIDAD_MEDIDA_CHOICES)
    stock_minimo = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    stock_actual = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def validar_stock(self, cantidad):
        """Valida si hay suficiente stock para una operación"""
        if cantidad < 0:
            raise ValidationError("La cantidad no puede ser negativa")
        if self.tipo_producto == 'MATERIA' and cantidad > self.stock_actual:
            raise ValidationError(f"Stock insuficiente. Stock actual: {self.stock_actual}")

    def ajustar_stock(self, cantidad, tipo_movimiento):
        """Ajusta el stock del producto según el tipo de movimiento"""
        if tipo_movimiento == 'ENTRADA':
            self.stock_actual = F('stock_actual') + cantidad
        elif tipo_movimiento == 'SALIDA':
            self.validar_stock(cantidad)
            self.stock_actual = F('stock_actual') - cantidad
        else:
            raise ValidationError("Tipo de movimiento no válido")
        
        self.save()
        self.refresh_from_db()  # Actualizar el valor de stock_actual

    def verificar_stock_minimo(self):
        """Verifica si el producto está por debajo del stock mínimo"""
        return self.stock_actual <= self.stock_minimo

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_producto_display()})"

    def clean(self):
        super().clean()
        if self.stock_minimo < 0:
            raise ValidationError("El stock mínimo no puede ser negativo")

class Lote(models.Model):
    numero_lote = models.CharField(max_length=50, unique=True)
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.PROTECT,
        limit_choices_to={'tipo_producto': 'MATERIA'}
    )
    peso_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    peso_procesado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('PENDIENTE', 'Pendiente de Procesar'),
            ('EN_PROCESO', 'En Proceso'),
            ('COMPLETADO', 'Procesamiento Completado')
        ],
        default='PENDIENTE'
    )
    
    def __str__(self):
        return f"Lote {self.numero_lote} - {self.producto.nombre}"

class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
        ('AJUSTE', 'Ajuste'),
        ('PROCESAMIENTO', 'Procesamiento de Materia Prima')
    ]

    producto = models.ForeignKey(
        'Producto',
        on_delete=models.PROTECT,
        related_name='movimientos'
    )
    tipo_movimiento = models.CharField(
        max_length=20,
        choices=TIPO_MOVIMIENTO_CHOICES
    )
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(
        'dashboard.Usuario',
        on_delete=models.PROTECT,
        related_name='movimientos_inventario'
    )
    stock_anterior = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    stock_resultante = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha_movimiento']

    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} - {self.producto.nombre} ({self.cantidad})"
    

