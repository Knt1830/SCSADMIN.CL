from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re

def validar_rut_chileno(rut):
    # Eliminar puntos y guión del RUT
    rut = rut.replace(".", "").replace("-", "")
    
    # Verificar formato básico
    if not re.match(r'^\d{7,8}[0-9K]$', rut):
        raise ValidationError(
            _('%(rut)s no es un RUT válido. Use formato: XX.XXX.XXX-X'),
            params={'rut': rut},
        )
    
    # Separar número y dígito verificador
    rut_numero = rut[:-1]
    dv_ingresado = rut[-1].upper()
    
    # Calcular dígito verificador
    multiplicador = 2
    suma = 0
    for d in reversed(rut_numero):
        suma += int(d) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2
    
    dv_calculado = str(11 - (suma % 11))
    if dv_calculado == '11':
        dv_calculado = '0'
    elif dv_calculado == '10':
        dv_calculado = 'K'
    
    if dv_calculado != dv_ingresado:
        raise ValidationError(
            _('El dígito verificador no es válido para este RUT.'),
            params={'rut': rut},
        )

class Trabajador(models.Model):
    CATEGORIA_CHOICES = [
        ('PL', 'Planta'),
        ('CO', 'Conductor'),
        ('CA', 'Carguero'),
        ('TE', 'Temporal'),
    ]
    
    nombre = models.CharField(
        max_length=200,
        help_text="Nombre completo del trabajador"
    )
    rut = models.CharField(
        max_length=12,
        unique=True,
        validators=[validar_rut_chileno],
        help_text="Formato: XX.XXX.XXX-X"
    )
    categoria = models.CharField(
        max_length=2,
        choices=CATEGORIA_CHOICES,
        help_text="Categoría del trabajador"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de registro del trabajador"
    )
    
    class Meta:
        verbose_name = "Trabajador"
        verbose_name_plural = "Trabajadores"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.rut}"
    
    def clean(self):
        # Formatear RUT si viene sin formato
        if self.rut and not re.match(r'^\d{1,2}\.\d{3}\.\d{3}-[\dK]$', self.rut):
            # Eliminar cualquier formato existente
            rut_limpio = re.sub(r'[^0-9Kk]', '', self.rut)
            
            if len(rut_limpio) < 2:
                raise ValidationError({'rut': 'RUT inválido'})
                
            # Formatear RUT
            dv = rut_limpio[-1]
            numero = rut_limpio[:-1]
            numero_formateado = ''
            
            for i, digito in enumerate(reversed(str(numero))):
                if i % 3 == 0 and i != 0:
                    numero_formateado = '.' + numero_formateado
                numero_formateado = digito + numero_formateado
            
            self.rut = f"{numero_formateado}-{dv}"

class PagoMensual(models.Model):
    ESTADO_CHOICES = [
        ('PE', 'Pendiente'),
        ('PA', 'Pagado'),
        ('AN', 'Anulado'),
    ]
    
    trabajador = models.ForeignKey(
        Trabajador,
        on_delete=models.PROTECT,
        related_name='pagos_mensuales',
        help_text="Trabajador al que corresponde el pago"
    )
    mes = models.DateField(
        help_text="Mes correspondiente al pago"
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        help_text="Monto del pago en pesos chilenos"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de registro del pago"
    )
    estado = models.CharField(
        max_length=2,
        choices=ESTADO_CHOICES,
        default='PE',
        help_text="Estado actual del pago"
    )
    
    class Meta:
        verbose_name = "Pago Mensual"
        verbose_name_plural = "Pagos Mensuales"
        ordering = ['-mes', 'trabajador']
        # Evitar pagos duplicados para el mismo trabajador en el mismo mes
        unique_together = ['trabajador', 'mes']
    
    def __str__(self):
        return f"Pago {self.mes.strftime('%m/%Y')} - {self.trabajador.nombre}"


class PagoTemporal(models.Model):
    ESTADO_CHOICES = [
        ('PE', 'Pendiente'),
        ('PA', 'Pagado'),
        ('AN', 'Anulado'),
    ]
    
    trabajador = models.ForeignKey(
        Trabajador,
        on_delete=models.PROTECT,
        related_name='pagos_temporales',
        help_text="Trabajador temporal al que corresponde el pago"
    )
    semana_inicio = models.DateField(
        help_text="Fecha de inicio de la semana"
    )
    semana_fin = models.DateField(
        help_text="Fecha de fin de la semana"
    )
    total_unidades = models.IntegerField(
        help_text="Total de unidades producidas en la semana"
    )
    monto_total = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        help_text="Monto total del pago en pesos chilenos"
    )
    estado = models.CharField(
        max_length=2,
        choices=ESTADO_CHOICES,
        default='PE',
        help_text="Estado actual del pago"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de registro del pago temporal"
    )
    
    class Meta:
        verbose_name = "Pago Temporal"
        verbose_name_plural = "Pagos Temporales"
        ordering = ['-semana_inicio', 'trabajador']
        unique_together = ['trabajador', 'semana_inicio', 'semana_fin']
    
    def __str__(self):
        return f"Pago Temporal {self.semana_inicio.strftime('%d/%m/%Y')} - {self.trabajador.nombre}"
    
    def clean(self):
        if self.semana_inicio and self.semana_fin:
            if self.semana_inicio > self.semana_fin:
                raise ValidationError({
                    'semana_inicio': 'La fecha de inicio no puede ser posterior a la fecha de fin'
                })
            # Verificar que el trabajador sea de categoría temporal
            if self.trabajador.categoria != 'TE':
                raise ValidationError({
                    'trabajador': 'Solo se pueden registrar pagos temporales para trabajadores de categoría Temporal'
                })


class ProduccionTemporal(models.Model):
    trabajador = models.ForeignKey(
        Trabajador,
        on_delete=models.PROTECT,
        related_name='producciones_temporales',
        help_text="Trabajador que realizó la producción"
    )
    producto = models.CharField(
        max_length=100,
        help_text="Nombre o código del producto"
    )
    cantidad = models.IntegerField(
        help_text="Cantidad de unidades producidas"
    )
    valor_unitario = models.DecimalField(
        max_digits=8,
        decimal_places=0,
        help_text="Valor por unidad en pesos chilenos"
    )
    fecha = models.DateField(
        help_text="Fecha de la producción"
    )
    total_calculado = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        help_text="Total calculado (cantidad * valor_unitario)"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de registro de la producción"
    )
    
    class Meta:
        verbose_name = "Producción Temporal"
        verbose_name_plural = "Producciones Temporales"
        ordering = ['-fecha', 'trabajador']
    
    def __str__(self):
        return f"Producción {self.fecha.strftime('%d/%m/%Y')} - {self.trabajador.nombre} - {self.producto}"
    
    def clean(self):
        # Verificar que el trabajador sea de categoría temporal
        if self.trabajador.categoria != 'TE':
            raise ValidationError({
                'trabajador': 'Solo se pueden registrar producciones para trabajadores de categoría Temporal'
            })
        
    def save(self, *args, **kwargs):
        # Calcular el total antes de guardar
        self.total_calculado = self.cantidad * self.valor_unitario
        super().save(*args, **kwargs)