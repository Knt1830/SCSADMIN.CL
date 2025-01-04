from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator
from produccion.models import ItemProduccion

class Trabajador(models.Model):
    TIPO_CHOICES = [
        ('PLANTA', 'Trabajador de Planta'),
        ('TEMPORERO', 'Trabajador Temporero'),
    ]

    BANCO_CHOICES = [
        ('ESTADO', 'Banco Estado'),
        ('CHILE', 'Banco de Chile'),
        ('BCI', 'Banco BCI'),
        ('SANTANDER', 'Banco Santander'),
        ('SCOTIABANK', 'Banco Scotiabank'),
        ('ITAU', 'Banco Itaú'),
        ('FALABELLA', 'Banco Falabella'),
        ('SECURITY', 'Banco Security')
    ]
    
    TIPO_CUENTA_CHOICES = [
        ('CORRIENTE', 'Cuenta Corriente'),
        ('VISTA', 'Cuenta Vista'),
        ('AHORRO', 'Cuenta de Ahorro'),
        ('RUT', 'Cuenta RUT')
    ]

    usuario = models.OneToOneField(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='perfil_trabajador'
    )
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        help_text="Tipo de trabajador (planta o temporero)"
    )
    rut = models.CharField(
        max_length=12,
        unique=True,
        help_text="RUT del trabajador con formato XX.XXX.XXX-X"
    )
    fecha_nacimiento = models.DateField()
    direccion = models.TextField()
    telefono = models.CharField(max_length=15)
    contacto_emergencia = models.CharField(
        max_length=100,
        help_text="Nombre y teléfono del contacto de emergencia"
    )
    estado = models.BooleanField(
        default=True,
        help_text="Estado activo/inactivo del trabajador"
    )
    fecha_ingreso = models.DateField(
        default=timezone.now
    )
    fecha_termino = models.DateField(
        null=True,
        blank=True
    )
    observaciones = models.TextField(
        blank=True
    )
    afp = models.CharField(
        max_length=50,
        blank=True, 
        null=True
    )
    sistema_salud = models.CharField(
        max_length=50, 
        blank=True, 
        null=True
    )
    plan_salud = models.CharField(
        max_length=100, 
        blank=True, 
        null=True
    )
    banco = models.CharField(
        max_length=50,
        choices=BANCO_CHOICES,
        null=True,
        blank=True
    )
    tipo_cuenta = models.CharField(
        max_length=50,
        choices=TIPO_CUENTA_CHOICES,
        null=True,
        blank=True
    )
    numero_cuenta = models.CharField(
        max_length=30,
        null=True,
        blank=True
    )
    

    def clean(self):
        if self.fecha_termino and self.fecha_termino < self.fecha_ingreso:
            raise ValidationError('La fecha de término no puede ser anterior a la fecha de ingreso')

    def __str__(self):
        return f"{self.usuario.get_full_name()} ({self.get_tipo_display()})"

    class Meta:
        verbose_name = "Trabajador"
        verbose_name_plural = "Trabajadores"
        ordering = ['usuario__last_name', 'usuario__first_name']

class ContratoTrabajador(models.Model):
    TIPO_CONTRATO_CHOICES = [
        ('INDEFINIDO', 'Contrato Indefinido'),
        ('PLAZO_FIJO', 'Plazo Fijo'),
    ]

    trabajador = models.ForeignKey(
        Trabajador,
        on_delete=models.PROTECT,
        related_name='contratos',
        limit_choices_to={'tipo': 'PLANTA'}
    )
    tipo_contrato = models.CharField(
        max_length=10,
        choices=TIPO_CONTRATO_CHOICES
    )
    fecha_inicio = models.DateField()
    fecha_termino = models.DateField(
        null=True,
        blank=True,
        help_text="Solo para contratos a plazo fijo"
    )
    salario_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    horas_semanales = models.PositiveSmallIntegerField(
        default=45,
        help_text="Horas de trabajo semanales acordadas"
    )
    bonificacion_colacion = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )
    bonificacion_movilidad = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )
    otros_bonos = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )
    activo = models.BooleanField(
        default=True
    )

    def clean(self):
        if self.fecha_termino and self.fecha_termino < self.fecha_inicio:
            raise ValidationError('La fecha de término no puede ser anterior a la fecha de inicio')
        
        # Validar que el trabajador sea de planta
        if self.trabajador.tipo != 'PLANTA':
            raise ValidationError('Solo los trabajadores de planta pueden tener contratos')

        # Validar que no haya otros contratos activos
        if self.activo:
            contratos_activos = ContratoTrabajador.objects.filter(
                trabajador=self.trabajador,
                activo=True
            ).exclude(id=self.id)
            if contratos_activos.exists():
                raise ValidationError('El trabajador ya tiene un contrato activo')

    class Meta:
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"
        ordering = ['-fecha_inicio']

class TarifaProduccion(models.Model):
    trabajador = models.ForeignKey(
        Trabajador,
        on_delete=models.PROTECT,
        related_name='tarifas',
        limit_choices_to={'tipo': 'TEMPORERO'}
    )
    producto = models.ForeignKey(
        'inventario.Producto',
        on_delete=models.PROTECT,
        related_name='tarifas'
    )
    precio_unidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Precio por unidad producida"
    )
    fecha_inicio = models.DateField(
        default=timezone.now
    )
    fecha_termino = models.DateField(
        null=True,
        blank=True
    )
    activa = models.BooleanField(
        default=True
    )

    def clean(self):
        if self.fecha_termino and self.fecha_termino < self.fecha_inicio:
            raise ValidationError('La fecha de término no puede ser anterior a la fecha de inicio')
        
        # Validar que el trabajador sea temporero
        if self.trabajador.tipo != 'TEMPORERO':
            raise ValidationError('Solo los trabajadores temporeros pueden tener tarifas de producción')

        # Validar que no haya otras tarifas activas para el mismo producto
        if self.activa:
            tarifas_activas = TarifaProduccion.objects.filter(
                trabajador=self.trabajador,
                producto=self.producto,
                activa=True
            ).exclude(id=self.id)
            if tarifas_activas.exists():
                raise ValidationError('Ya existe una tarifa activa para este producto')

    class Meta:
        verbose_name = "Tarifa de Producción"
        verbose_name_plural = "Tarifas de Producción"
        ordering = ['trabajador', 'producto', '-fecha_inicio']
        unique_together = ['trabajador', 'producto', 'fecha_inicio']

class AsistenciaTrabajador(models.Model):
    trabajador = models.ForeignKey(
        Trabajador,
        on_delete=models.PROTECT,
        related_name='asistencias',
        limit_choices_to={'tipo': 'PLANTA'}
    )
    fecha = models.DateField()
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField(
        null=True,
        blank=True
    )
    horas_extra = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0,
        help_text="Horas extras trabajadas"
    )
    observaciones = models.TextField(
        blank=True
    )

    def clean(self):
        # Validar que el trabajador sea de planta
        if self.trabajador.tipo != 'PLANTA':
            raise ValidationError('Solo se puede registrar asistencia para trabajadores de planta')
        
        # Validar que no exista otro registro para el mismo día
        if AsistenciaTrabajador.objects.filter(
            trabajador=self.trabajador,
            fecha=self.fecha
        ).exclude(id=self.id).exists():
            raise ValidationError('Ya existe un registro de asistencia para esta fecha')

        # Validar hora de salida posterior a entrada
        if self.hora_salida and self.hora_entrada > self.hora_salida:
            raise ValidationError('La hora de salida debe ser posterior a la hora de entrada')

    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        ordering = ['-fecha', '-hora_entrada']
        unique_together = ['trabajador', 'fecha']

# Nota: ProduccionTrabajador no se incluye aquí ya que está manejado 
# por el módulo de Producción a través de ProduccionDiaria e ItemProduccion

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model

class PeriodoLiquidacion(models.Model):
    """Periodo para agrupar liquidaciones"""
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(
        max_length=20,
        choices=[
            ('ABIERTO', 'Abierto'),
            ('CERRADO', 'Cerrado'),
            ('PROCESANDO', 'Procesando'),
            ('PAGADO', 'Pagado')
        ],
        default='ABIERTO'
    )
    fecha_pago = models.DateField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True)

    def clean(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError('La fecha de fin no puede ser anterior a la fecha de inicio')
        
        # Verificar que no haya solapamiento de períodos
        periodos_solapados = PeriodoLiquidacion.objects.filter(
            fecha_inicio__lte=self.fecha_fin,
            fecha_fin__gte=self.fecha_inicio
        ).exclude(id=self.id)
        
        if periodos_solapados.exists():
            raise ValidationError('El período se solapa con otro período existente')

    class Meta:
        ordering = ['-fecha_inicio']
        verbose_name = "Período de Liquidación"
        verbose_name_plural = "Períodos de Liquidación"

    def __str__(self):
        return f"Período {self.fecha_inicio} - {self.fecha_fin}"

class Liquidacion(models.Model):
    """Liquidación individual por trabajador"""
    periodo = models.ForeignKey(
        PeriodoLiquidacion,
        on_delete=models.PROTECT,
        related_name='liquidaciones'
    )
    trabajador = models.ForeignKey(
        'Trabajador',
        on_delete=models.PROTECT,
        related_name='liquidaciones'
    )
    estado = models.CharField(
        max_length=20,
        choices=[
            ('BORRADOR', 'Borrador'),
            ('REVISADA', 'Revisada'),
            ('APROBADA', 'Aprobada'),
            ('RECHAZADA', 'Rechazada'),
            ('PAGADA', 'Pagada')
        ],
        default='BORRADOR'
    )
    
    # Campos para trabajadores de planta
    sueldo_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    dias_trabajados = models.PositiveSmallIntegerField(default=0)
    horas_extra = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Bonificaciones y descuentos
    bonificacion_colacion = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )
    bonificacion_movilidad = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )
    otros_bonos = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )
    
    # Campos comunes
    total_haberes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    total_descuentos = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    total_liquido = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Trazabilidad
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_revision = models.DateTimeField(null=True, blank=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    revisado_por = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='liquidaciones_revisadas',
        null=True,
        blank=True
    )
    aprobado_por = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='liquidaciones_aprobadas',
        null=True,
        blank=True
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        unique_together = ['periodo', 'trabajador']
        ordering = ['-periodo__fecha_inicio', 'trabajador__usuario__last_name']
        verbose_name = "Liquidación"
        verbose_name_plural = "Liquidaciones"

    def clean(self):
        if self.estado in ['APROBADA', 'PAGADA'] and self.periodo.estado == 'ABIERTO':
            raise ValidationError('No se puede aprobar/pagar una liquidación de un período abierto')
    
    def calcular_totales(self):
        """Calcula los totales basados en el tipo de trabajador"""
        if self.trabajador.tipo == 'PLANTA':
            self.calcular_totales_planta()
        else:
            self.calcular_totales_temporero()
            
    def calcular_totales_planta(self):
        """Calcula totales para trabajador de planta"""
        # Calcular sueldo base proporcional
        sueldo_proporcional = (self.sueldo_base / 30) * self.dias_trabajados
        
        # Calcular valor hora extra
        valor_hora = self.sueldo_base / 180  # 45 horas semanales * 4 semanas
        total_horas_extra = self.horas_extra * (valor_hora * 1.5)  # 50% recargo
        
        # Sumar haberes
        self.total_haberes = (
            sueldo_proporcional +
            total_horas_extra +
            self.bonificacion_colacion +
            self.bonificacion_movilidad +
            self.otros_bonos
        )
        
        # Por ahora los descuentos son 0, se implementarán después
        self.total_descuentos = 0
        
        # Calcular líquido
        self.total_liquido = self.total_haberes - self.total_descuentos
        
    def calcular_totales_temporero(self):
        """Calcula totales para trabajador temporero"""
        # Obtener todas las producciones del período
        producciones = ItemProduccion.objects.filter(
            produccion__trabajador=self.trabajador.usuario,
            produccion__fecha__range=[self.periodo.fecha_inicio, self.periodo.fecha_fin]
        ).select_related('produccion')
        
        # Sumar todas las producciones
        totales = producciones.aggregate(
            total=models.Sum(
                models.F('cantidad_producida') * models.F('precio_unidad')
            )
        )
        
        self.total_haberes = totales['total'] or 0
        self.total_descuentos = 0  # Por ahora
        self.total_liquido = self.total_haberes - self.total_descuentos

    def save(self, *args, **kwargs):
        # Calcular totales antes de guardar
        self.calcular_totales()
        super().save(*args, **kwargs)

class DetalleDescuentos(models.Model):
    """Detalle de descuentos aplicados a una liquidación"""
    liquidacion = models.ForeignKey(
        Liquidacion,
        on_delete=models.CASCADE,
        related_name='descuentos'
    )
    concepto = models.CharField(max_length=100)
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    obligatorio = models.BooleanField(
        default=True,
        help_text="Indica si es un descuento legal obligatorio"
    )
    observacion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Detalle de Descuento"
        verbose_name_plural = "Detalles de Descuentos"

class DetalleBonificacion(models.Model):
    """Detalle de bonificaciones adicionales"""
    liquidacion = models.ForeignKey(
        Liquidacion,
        on_delete=models.CASCADE,
        related_name='bonificaciones'
    )
    concepto = models.CharField(max_length=100)
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    permanente = models.BooleanField(
        default=False,
        help_text="Indica si la bonificación es permanente"
    )
    observacion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Detalle de Bonificación"
        verbose_name_plural = "Detalles de Bonificaciones"