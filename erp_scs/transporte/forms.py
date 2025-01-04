from django import forms
from .models import Vehiculo, Chofer, GastoVehiculo

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['modelo', 'marca', 'patente', 'color', 'año', 'kilometraje_actual']
        widgets = {
            'modelo': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'marca': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'patente': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'color': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'año': forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'kilometraje_actual': forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
        }

class ChoferForm(forms.ModelForm):
    class Meta:
        model = Chofer
        fields = ['nombre', 'rut', 'telefono', 'vehiculo_asignado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'rut': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'telefono': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'vehiculo_asignado': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
        }

class GastoVehiculoForm(forms.ModelForm):
    class Meta:
        model = GastoVehiculo
        fields = ['vehiculo', 'tipo', 'monto', 'kilometraje', 'litros']
        widgets = {
            'vehiculo': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'tipo': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'monto': forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'kilometraje': forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'placeholder': 'Opcional para tipos de gasto distintos a combustible'}),
            'litros': forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'placeholder': 'Solo para gastos de combustible'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        litros = cleaned_data.get('litros')
        kilometraje = cleaned_data.get('kilometraje')

        # Validaciones específicas para gastos de combustible
        if tipo == 'combustible':
            if not litros:
                self.add_error('litros', 'Los litros son obligatorios para gastos de combustible')
            if not kilometraje:
                self.add_error('kilometraje', 'El kilometraje es obligatorio para gastos de combustible')

        return cleaned_data