# forms.py
from django import forms
from .models import Lote, ProduccionDiaria, ItemProduccion
from compras.models import OrdenCompra
from django.forms import inlineformset_factory
from django.db.models import Q
from django.core.exceptions import ValidationError
from produccion.models import MateriaPrimaUtilizada



class LoteForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = ['codigo', 'orden_compra', 'estado', 'observaciones']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Obtener el instance actual (si existe)
        instance = kwargs.get('instance')
        
        # Construir el queryset base
        queryset = OrdenCompra.objects.filter(estado='RECIBIDA')
        
        # Si estamos editando, incluir la orden actual aunque ya tenga lote
        if instance:
            queryset = queryset.filter(
                Q(lotes__isnull=True) | 
                Q(id=instance.orden_compra_id)
            )
        else:
            queryset = queryset.filter(lotes__isnull=True)
            
        self.fields['orden_compra'].queryset = queryset.order_by('-fecha_emision')
        self.fields['orden_compra'].empty_label = "Seleccione una orden de compra"
        
        # Agregar clases de estilo
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            })
            
        self.fields['orden_compra'].queryset = queryset.order_by('-fecha_emision')
        self.fields['orden_compra'].empty_label = "Seleccione una orden de compra"
        
        # Agregar clases de estilo
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            })
class MateriaPrimaFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if not self.forms:
            raise forms.ValidationError('Debe especificar al menos una materia prima')
        
        # Validar stock disponible
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                producto = form.cleaned_data.get('producto')
                cantidad = form.cleaned_data.get('cantidad')
                if producto and cantidad:
                    try:
                        producto.validar_stock(cantidad)
                    except ValidationError as e:
                        form.add_error('cantidad', str(e))

MateriaPrimaUtilizadaFormSet = inlineformset_factory(
    ProduccionDiaria,
    MateriaPrimaUtilizada,
    formset=MateriaPrimaFormSet,
    fields=['producto', 'cantidad'],
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)

class ProduccionDiariaForm(forms.ModelForm):
    class Meta:
        model = ProduccionDiaria
        fields = ['lote', 'trabajador', 'fecha', 'hora_inicio', 'hora_fin', 'merma_kg', 'observaciones']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time'}),
            'merma_kg': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hora_fin'].required = False
        self.fields['merma_kg'].required = False
        self.fields['observaciones'].required = False

class ItemProduccionForm(forms.ModelForm):
    class Meta:
        model = ItemProduccion
        fields = ['producto', 'cantidad_producida', 'precio_unidad', 'calidad']
        widgets = {
            'producto': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'cantidad_producida': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'min': '0',
                'step': '0.01'
            }),
            'precio_unidad': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'min': '0',
                'step': '0.01'
            }),
            'calidad': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obtener productos del inventario
        from inventario.models import Producto
        self.fields['producto'].queryset = Producto.objects.filter(activo=True)

# Creamos el formset para ItemProduccion
ItemProduccionFormSet = forms.inlineformset_factory(
    ProduccionDiaria, 
    ItemProduccion,
    form=ItemProduccionForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)