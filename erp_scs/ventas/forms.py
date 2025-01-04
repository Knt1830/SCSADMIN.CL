# ventas/forms.py
from django import forms
from .models import Cliente, Venta, DetalleVenta
from inventario.models import Producto

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'rut', 'telefono', 'direccion', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'rut': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'telefono': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'direccion': forms.Textarea(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
        }

    def clean_rut(self):
        rut = self.cleaned_data['rut']
        # Aquí podrías añadir validación específica de RUT chileno
        return rut

class VentaForm(forms.ModelForm):
    # Campo para indicar si el cliente es existente o nuevo
    cliente_existente = forms.BooleanField(
        required=False, 
        initial=True,
        label='Cliente Existente',
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'})
    )

    class Meta:
        model = Venta
        fields = ['es_credito', 'dias_credito', 'observaciones']
        widgets = {
            'es_credito': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}),
            'dias_credito': forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'observaciones': forms.Textarea(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'rows': 3}),
        }

class DetalleVentaForm(forms.ModelForm):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True, tipo_producto='VENTA'),
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
    )
    
    class Meta:
        model = DetalleVenta
        fields = ['producto', 'cantidad', 'precio_unitario']
        widgets = {
            'cantidad': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 
                'step': '0.01', 
                'min': '0.01'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 
                'step': '0.01', 
                'min': '0.01'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')
        
        if producto and cantidad:
            # Validar stock disponible
            if cantidad > producto.stock_actual:
                raise forms.ValidationError(f"Stock insuficiente. Stock actual de {producto.nombre}: {producto.stock_actual}")
        
        return cleaned_data

DetalleVentaFormSet = forms.inlineformset_factory(
    Venta, 
    DetalleVenta, 
    form=DetalleVentaForm,
    extra=1,
    can_delete=True,
    fields=['producto', 'cantidad', 'precio_unitario'],
    min_num=1,
    validate_min=True
)