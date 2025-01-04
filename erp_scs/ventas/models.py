# ventas/models.py
from django.db import models
from django.utils import timezone
from dashboard.models import Usuario

class Cliente(models.Model):
    """
    Modelo para representar clientes del sistema
    """
    TIPO_DOCUMENTO_CHOICES = [
        ('RUT', 'RUT'),
        # Pueden agregarse más tipos de documento según sea necesario
    ]

    nombre = models.CharField(max_length=200, verbose_name='Nombre Completo')
    rut = models.CharField(max_length=20, unique=True, verbose_name='RUT')
    telefono = models.CharField(max_length=20, verbose_name='Teléfono')
    direccion = models.TextField(blank=True, null=True, verbose_name='Dirección')
    email = models.EmailField(blank=True, null=True, verbose_name='Correo Electrónico')
    
    # Campos de seguimiento
    fecha_registro = models.DateTimeField(auto_now_add=True)
    usuario_registro = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='clientes_registrados')

    def __str__(self):
        return f"{self.nombre} (RUT: {self.rut})"

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre']

class Venta(models.Model):
    """
    Modelo para registrar ventas
    """
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADA', 'Pagada'),
        ('ANULADA', 'Anulada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='ventas')
    fecha_venta = models.DateTimeField(default=timezone.now)
    usuario_venta = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='ventas_realizadas')
    
    # Campos para ventas a crédito
    es_credito = models.BooleanField(default=False, verbose_name='Venta a Crédito')
    dias_credito = models.IntegerField(null=True, blank=True, verbose_name='Días de Crédito')
    fecha_vencimiento_credito = models.DateField(null=True, blank=True)
    
    # Estado y montos
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    total_venta = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Campos adicionales
    observaciones = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Si es una venta a crédito, calcular fecha de vencimiento
        if self.es_credito and self.dias_credito:
            self.fecha_vencimiento_credito = timezone.now().date() + timezone.timedelta(days=self.dias_credito)
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Venta {self.id} - {self.cliente.nombre} - {self.fecha_venta}"

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha_venta']

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    
    producto = models.ForeignKey('inventario.Producto', on_delete=models.PROTECT)
    nombre_producto = models.CharField(max_length=200)
    
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # Calcular subtotal antes de guardar
        self.subtotal = self.cantidad * self.precio_unitario
        
        # Asegurarse de que el nombre del producto coincida
        self.nombre_producto = self.producto.nombre
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre_producto} - Venta {self.venta.id}"

class CreditoCliente(models.Model):
    """
    Modelo para registrar y rastrear deudas de clientes
    """
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='creditos')
    venta = models.OneToOneField(Venta, on_delete=models.CASCADE)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    fecha_credito = models.DateTimeField(default=timezone.now)
    fecha_vencimiento = models.DateField()
    
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PARCIAL', 'Pago Parcial'),
        ('PAGADO', 'Pagado'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')

    def __str__(self):
        return f"Crédito de {self.cliente.nombre} - {self.estado}"

    @property
    def monto_pendiente(self):
        return self.monto_total - self.monto_pagado

    class Meta:
        verbose_name = 'Crédito de Cliente'
        verbose_name_plural = 'Créditos de Clientes'
        ordering = ['-fecha_credito']

class PagoCredito(models.Model):
    credito = models.ForeignKey(CreditoCliente, on_delete=models.PROTECT, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True)
    usuario = models.ForeignKey('dashboard.Usuario', on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Pago de Crédito"
        verbose_name_plural = "Pagos de Créditos"
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago de ${self.monto} - {self.credito.cliente.nombre}"
