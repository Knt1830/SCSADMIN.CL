from django import forms
from .models import Trabajador, PagoMensual, ProduccionTemporal

class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = ['nombre', 'rut', 'categoria']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'rut': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg',
                'placeholder': 'XX.XXX.XXX-X'
            }),
            'categoria': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'})
        }

class PagoMensualForm(forms.ModelForm):
    class Meta:
        model = PagoMensual
        fields = ['trabajador', 'mes', 'monto', 'estado']
        widgets = {
            'trabajador': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'mes': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg',
                'type': 'month'
            }),
            'monto': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'estado': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar trabajadores excluyendo temporales
        self.fields['trabajador'].queryset = Trabajador.objects.exclude(categoria='TE')

class ProduccionTemporalForm(forms.ModelForm):
    class Meta:
        model = ProduccionTemporal
        fields = ['trabajador', 'producto', 'cantidad', 'valor_unitario', 'fecha']
        widgets = {
            'trabajador': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'producto': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'cantidad': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'valor_unitario': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'fecha': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg',
                'type': 'date'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo trabajadores temporales
        self.fields['trabajador'].queryset = Trabajador.objects.filter(categoria='TE')