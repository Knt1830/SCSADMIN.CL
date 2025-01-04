from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from .models import Trabajador, ContratoTrabajador, TarifaProduccion

User = get_user_model()

class TrabajadorForm(forms.ModelForm):
    # Campos para el usuario
    first_name = forms.CharField(
        label='Nombres',
        max_length=150,
        required=True
    )
    last_name = forms.CharField(
        label='Apellidos',
        max_length=150,
        required=True
    )
    email = forms.EmailField(
        label='Correo electrónico',
        required=True
    )

    
    SISTEMA_SALUD_CHOICES = [
        ('FONASA', 'Fonasa'),
        ('ISAPRE', 'Isapre'),
    ]
    
    AFP_CHOICES = [
        ('CAPITAL', 'AFP Capital'),
        ('CUPRUM', 'AFP Cuprum'),
        ('HABITAT', 'AFP Habitat'),
        ('MODELO', 'AFP Modelo'),
        ('PLANVITAL', 'AFP PlanVital'),
        ('PROVIDA', 'AFP ProVida'),
        ('UNO', 'AFP Uno'),
    ]

    first_name = forms.CharField(label='Nombres', max_length=150, required=True)
    last_name = forms.CharField(label='Apellidos', max_length=150, required=True)
    email = forms.EmailField(label='Correo electrónico', required=True)
    afp = forms.ChoiceField(choices=AFP_CHOICES, required=False)
    sistema_salud = forms.ChoiceField(choices=SISTEMA_SALUD_CHOICES, required=False)
    plan_salud = forms.CharField(max_length=100, required=False)

    class Meta:
       model = Trabajador
       fields = [
           'tipo', 'rut', 'fecha_nacimiento', 'direccion',
           'telefono', 'contacto_emergencia', 'estado',
           'fecha_ingreso', 'fecha_termino', 'observaciones',
           'afp', 'sistema_salud', 'plan_salud',
           'banco', 'tipo_cuenta', 'numero_cuenta'
       ]
       widgets = {
           'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
           'fecha_ingreso': forms.DateInput(attrs={'type': 'date'}),
           'fecha_termino': forms.DateInput(attrs={'type': 'date'}),
           'observaciones': forms.Textarea(attrs={'rows': 3}),
       }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Si estamos editando, prellenar los campos del usuario
            self.fields['first_name'].initial = self.instance.usuario.first_name
            self.fields['last_name'].initial = self.instance.usuario.last_name
            self.fields['email'].initial = self.instance.usuario.email
            
            # El tipo de trabajador no se puede cambiar una vez creado
            self.fields['tipo'].disabled = True
        
        # Agregar clases de Tailwind a todos los campos
        for field in self.fields.values():
            if isinstance(field.widget, forms.TextInput) or \
               isinstance(field.widget, forms.EmailInput) or \
               isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update({
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md'
                })
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'class': 'shadow-sm focus:ring-blue-500 focus:border-blue-500 mt-1 block w-full sm:text-sm border-gray-300 rounded-md'
                })

    def clean_rut(self):
        rut = self.cleaned_data['rut']
        # Aquí podrías agregar la validación específica del formato RUT
        return rut

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('fecha_termino'):
            if cleaned_data['fecha_termino'] < cleaned_data['fecha_ingreso']:
                raise ValidationError('La fecha de término no puede ser anterior a la fecha de ingreso')
        return cleaned_data

    def save(self, commit=True):
        trabajador = super().save(commit=False)
        
        # Crear o actualizar usuario
        if not trabajador.pk:
            # Crear nuevo usuario
            usuario = User.objects.create(
                username=self.cleaned_data['rut'],  # Usar RUT como username
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name']
            )
            trabajador.usuario = usuario
        else:
            # Actualizar usuario existente
            trabajador.usuario.first_name = self.cleaned_data['first_name']
            trabajador.usuario.last_name = self.cleaned_data['last_name']
            trabajador.usuario.email = self.cleaned_data['email']
            trabajador.usuario.save()
        
        if commit:
            trabajador.save()
        return trabajador

class ContratoTrabajadorForm(forms.ModelForm):
    class Meta:
        model = ContratoTrabajador
        fields = [
            'tipo_contrato', 'fecha_inicio', 'fecha_termino',
            'salario_base', 'horas_semanales', 'bonificacion_colacion',
            'bonificacion_movilidad', 'otros_bonos', 'activo'
        ]
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_termino': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, (forms.NumberInput, forms.TextInput, forms.DateInput)):
                field.widget.attrs.update({
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md'
                })

class TarifaProduccionForm(forms.ModelForm):
    class Meta:
        model = TarifaProduccion
        fields = ['producto', 'precio_unidad', 'fecha_inicio', 'fecha_termino', 'activa']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_termino': forms.DateInput(attrs={'type': 'date'}),
            'precio_unidad': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = self.fields['producto'].queryset.filter(
            activo=True
        ).order_by('nombre')
        
        for field in self.fields.values():
            if isinstance(field.widget, (forms.NumberInput, forms.TextInput, forms.DateInput)):
                field.widget.attrs.update({
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md'
                })

# Crear formset para tarifas de producción
TarifaProduccionFormSet = inlineformset_factory(
    Trabajador,
    TarifaProduccion,
    form=TarifaProduccionForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)