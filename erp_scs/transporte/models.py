from django.db import models
from django.core.validators import RegexValidator

class Vehiculo(models.Model):
    COLORES = [
        ('blanco', 'Blanco'),
        ('negro', 'Negro'),
        ('gris', 'Gris'),
        ('rojo', 'Rojo'),
        ('azul', 'Azul'),
        ('verde', 'Verde'),
    ]

    modelo = models.CharField(max_length=100)
    marca = models.CharField(max_length=100)
    patente = models.CharField(
        max_length=10, 
        unique=True, 
    )
    def clean(self):
        # Convertir la patente a mayúsculas antes de la validación
        if self.patente:
            self.patente = self.patente.upper()
        super().clean()

    color = models.CharField(max_length=20, choices=COLORES)
    año = models.PositiveIntegerField()
    kilometraje_actual = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    estado = models.CharField(
        max_length=20, 
        choices=[
            ('disponible', 'Disponible'),
            ('en_uso', 'En Uso'),
            ('mantenimiento', 'En Mantenimiento')
        ],
        default='disponible'
    )

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.patente})"

class GastoVehiculo(models.Model):
    TIPOS_GASTO = [
        ('combustible', 'Combustible'),
        ('reparacion', 'Reparación'),
        ('peaje', 'Peaje'),
    ]

    vehiculo = models.ForeignKey(
        Vehiculo, 
        on_delete=models.CASCADE, 
        related_name='gastos'
    )
    tipo = models.CharField(max_length=20, choices=TIPOS_GASTO)
    fecha = models.DateTimeField(auto_now_add=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Campos específicos para gastos de combustible
    kilometraje = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    litros = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True
    )

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.vehiculo} - {self.fecha}"

    def save(self, *args, **kwargs):
        # Si es un gasto de combustible y se proporciona kilometraje
        if self.tipo == 'combustible' and self.kilometraje:
            # Actualizar el kilometraje del vehículo
            vehiculo = self.vehiculo
            vehiculo.kilometraje_actual = max(
                vehiculo.kilometraje_actual, 
                self.kilometraje
            )
            vehiculo.save()
        
        super().save(*args, **kwargs)

class Chofer(models.Model):
    nombre = models.CharField(max_length=200)
    rut = models.CharField(
        max_length=12, 
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{1,2}\.\d{3}\.\d{3}[-][0-9kK]$',
                message='Formato de RUT inválido'
            )
        ]
    )
    telefono = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?569\d{8}$',
                message='Número de teléfono debe ser chileno'
            )
        ]
    )
    vehiculo_asignado = models.OneToOneField(
        Vehiculo, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='chofer_actual'
    )

    def __str__(self):
        return f"{self.nombre} (RUT: {self.rut})"

    def asignar_vehiculo(self, vehiculo):
        """
        Método para asignar un vehículo al chofer
        """
        # Si el chofer ya tiene un vehículo asignado, liberar ese vehículo
        if self.vehiculo_asignado:
            self.vehiculo_asignado.estado = 'disponible'
            self.vehiculo_asignado.save()
        
        # Asignar nuevo vehículo
        self.vehiculo_asignado = vehiculo
        vehiculo.estado = 'en_uso'
        vehiculo.save()
        self.save()
