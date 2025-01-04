# compras/forms.py
from django import forms
from .models import (
    TipoProveedor, 
    Proveedor, 
    ProveedorProducto, 
    OrdenCompra, 
    DetalleOrdenCompra, 
)
from inventario.models import Producto

class TipoProveedorForm(forms.ModelForm):
    class Meta:
        model = TipoProveedor
        fields = ['nombre', 'descripcion', 'es_materia_prima', 'activo']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            })

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'rut', 'direccion', 'telefono', 'tipo_proveedor']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_proveedor'].queryset = TipoProveedor.objects.filter(activo=True)
        self.fields['tipo_proveedor'].empty_label = "Seleccione un tipo de proveedor"
        
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            })

class ProveedorProductoForm(forms.ModelForm):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True),
        empty_label="Seleccione un producto"
    )

    class Meta:
        model = ProveedorProducto
        fields = ['producto', 'precio_referencia', 'es_proveedor_principal', 'notas']
        widgets = {
            'precio_referencia': forms.NumberInput(
                attrs={'step': '0.01', 'min': '0'}
            ),
            'notas': forms.Textarea(
                attrs={'rows': 3}
            )
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            })
            
        # Filtrar productos según el tipo de proveedor
        if hasattr(self, 'instance') and self.instance.proveedor_id:
            if self.instance.proveedor.tipo_proveedor.es_materia_prima:
                self.fields['producto'].queryset = Producto.objects.filter(
                    tipo_producto='MATERIA',
                    activo=True
                )
            else:
                self.fields['producto'].queryset = Producto.objects.exclude(
                    tipo_producto='MATERIA'
                ).filter(activo=True)

class OrdenCompraForm(forms.ModelForm):
    class Meta:
        model = OrdenCompra
        fields = ['proveedor', 'fecha_emision', 'fecha_entrega_esperada', 'notas']
        widgets = {
            'fecha_emision': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                }
            ),
            'fecha_entrega_esperada': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                }
            ),
            'notas': forms.Textarea(
                attrs={
                    'rows': 3,
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True)
        self.fields['proveedor'].widget.attrs.update({
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })

class DetalleOrdenCompraForm(forms.ModelForm):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True),
        empty_label="Seleccione un producto"
    )

    class Meta:
        model = DetalleOrdenCompra
        fields = ['producto', 'cantidad', 'precio_unitario', 'notas']
        widgets = {
            'cantidad': forms.NumberInput(
                attrs={
                    'step': '0.01',
                    'min': '0.01',
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                }
            ),
            'precio_unitario': forms.NumberInput(
                attrs={
                    'step': '0.01',
                    'min': '0.01',
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                }
            ),
            'notas': forms.Textarea(
                attrs={
                    'rows': 2,
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si la orden tiene un proveedor, filtrar productos según el tipo de proveedor
        if hasattr(self, 'instance') and self.instance.orden_compra_id:
            proveedor = self.instance.orden_compra.proveedor
            if proveedor.tipo_proveedor.es_materia_prima:
                self.fields['producto'].queryset = Producto.objects.filter(
                    tipo_producto='MATERIA',
                    activo=True
                )
            else:
                self.fields['producto'].queryset = Producto.objects.exclude(
                    tipo_producto='MATERIA'
                ).filter(activo=True)

    def clean(self):
        cleaned_data = super().clean()
        cantidad = cleaned_data.get('cantidad')
        precio_unitario = cleaned_data.get('precio_unitario')

        if cantidad is not None and cantidad <= 0:
            raise forms.ValidationError('La cantidad debe ser mayor que cero')
        
        if precio_unitario is not None and precio_unitario <= 0:
            raise forms.ValidationError('El precio unitario debe ser mayor que cero')

        return cleaned_data