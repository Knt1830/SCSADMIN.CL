from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Q
from .models import Lote, ProduccionDiaria
from .forms import LoteForm, ProduccionDiariaForm, ItemProduccionFormSet, MateriaPrimaUtilizadaFormSet
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from compras.models import OrdenCompra
import logging
logger = logging.getLogger('produccion') 
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction



class LoteListView(LoginRequiredMixin, ListView):
    model = Lote
    template_name = 'produccion/lote_list.html'
    context_object_name = 'lotes'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.GET.get('estado', '')
        search = self.request.GET.get('search', '')

        if estado:
            queryset = queryset.filter(estado=estado)
        
        if search:
            queryset = queryset.filter(
                Q(codigo__icontains=search) |
                Q(orden_compra__codigo__icontains=search)
            )
        
        return queryset.order_by('-fecha_creacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = Lote.ESTADO_CHOICES
        context['estado_actual'] = self.request.GET.get('estado', '')
        context['search'] = self.request.GET.get('search', '')
        return context

class LoteCreateView(LoginRequiredMixin, CreateView):
    model = Lote
    form_class = LoteForm
    template_name = 'produccion/lote_create.html'
    success_url = reverse_lazy('produccion:lote_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener últimas órdenes de compra que no tienen lote asociado
        context['ordenes_compra'] = OrdenCompra.objects.filter(
            estado='RECIBIDA',  # Solo órdenes recibidas
            lotes__isnull=True  # Solo órdenes sin lotes asociados
        ).select_related('proveedor').order_by('-fecha_creacion')
        return context
    
        
    


    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Lote creado exitosamente.')
        return super().form_valid(form)

class LoteUpdateView(LoginRequiredMixin, UpdateView):
    model = Lote
    form_class = LoteForm
    template_name = 'produccion/lote_create.html'
    success_url = reverse_lazy('produccion:lote_list')

    def form_valid(self, form):
        messages.success(self.request, 'Lote actualizado exitosamente.')
        return super().form_valid(form)

class LoteDetailView(LoginRequiredMixin, DetailView):
    model = Lote
    template_name = 'produccion/lote_detail.html'
    context_object_name = 'lote'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['producciones'] = self.object.producciones.all().order_by('-fecha')
        return context

# Vistas para Producción Diaria
class ProduccionListView(LoginRequiredMixin, ListView):
    model = ProduccionDiaria
    template_name = 'produccion/produccion_list.html'
    context_object_name = 'producciones'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        lote_id = self.request.GET.get('lote', '')
        fecha = self.request.GET.get('fecha', '')

        if lote_id:
            queryset = queryset.filter(lote_id=lote_id)
        if fecha:
            queryset = queryset.filter(fecha=fecha)

        return queryset.order_by('-fecha', '-hora_inicio')

class ProduccionCreateView(LoginRequiredMixin, CreateView):
    model = ProduccionDiaria
    form_class = ProduccionDiariaForm
    template_name = 'produccion/produccion_create.html'
    
    def get_success_url(self):
        return reverse_lazy('produccion:lote_detail', kwargs={'pk': self.object.lote.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['items_formset'] = ItemProduccionFormSet(self.request.POST)
            context['materias_primas_formset'] = MateriaPrimaUtilizadaFormSet(self.request.POST)
        else:
            context['items_formset'] = ItemProduccionFormSet()
            context['materias_primas_formset'] = MateriaPrimaUtilizadaFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context['items_formset']
        materias_primas_formset = context['materias_primas_formset']
        
        # Validar formsets fuera de la transacción
        if not items_formset.is_valid():
            messages.error(self.request, "Hay errores en los items de producción")
            return self.form_invalid(form)
            
        if not materias_primas_formset.is_valid():
            messages.error(self.request, "Hay errores en las materias primas")
            return self.form_invalid(form)

        # Iniciar transacción atómica
        try:
            with transaction.atomic():
                # 1. Guardar la producción
                self.object = form.save(commit=False)
                self.object.estado = 'PENDIENTE'
                self.object.save()
                
                # 2. Guardar los formsets
                items_formset.instance = self.object
                materias_primas_formset.instance = self.object
                items_formset.save()
                materias_primas_formset.save()
                
                # 3. Validar stock disponible
                self.object.validar_stock_materias_primas()
                
                # 4. Procesar inventario
                self.object.procesar_inventario()
                
                messages.success(self.request, 'Producción registrada exitosamente')
                return redirect(self.get_success_url())
                
        except ValidationError as e:
            messages.error(self.request, str(e))
            # No necesitamos hacer rollback explícito aquí, transaction.atomic() lo maneja
            return self.form_invalid(form)
            
        except Exception as e:
            logger.exception("Error al procesar la producción")
            messages.error(self.request, f"Error al procesar la producción: {str(e)}")
            # No necesitamos hacer rollback explícito aquí, transaction.atomic() lo maneja
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Por favor corrija los errores en el formulario")
        return super().form_invalid(form)
    
class ProduccionDiariaForm(forms.ModelForm):
    class Meta:
        model = ProduccionDiaria
        fields = ['lote', 'trabajador', 'fecha', 'hora_inicio', 'hora_fin', 'merma_kg', 'observaciones']
        widgets = {
            'fecha': forms.DateInput(attrs={
                'type': 'date',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'hora_inicio': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'hora_fin': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'merma_kg': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'step': '0.01',
                'min': '0'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 3
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar el campo merma_kg
        self.fields['merma_kg'].required = False
        self.fields['merma_kg'].initial = 0
        
        # Hacer el campo hora_fin opcional
        self.fields['hora_fin'].required = False
        
        # Hacer observaciones opcional
        self.fields['observaciones'].required = False
        
        # Configurar el queryset de trabajadores
        self.fields['trabajador'].queryset = self.fields['trabajador'].queryset.filter(
            is_active=True,
            groups__name__in=['Temporeros', 'Trabajador', 'trabajador']
        ).exclude(
            is_staff=True
        ).distinct()
        
        # Agregar clases de estilo a lote y trabajador
        self.fields['lote'].widget.attrs.update({
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
        self.fields['trabajador'].widget.attrs.update({
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
        
    def clean_merma_kg(self):
        merma_kg = self.cleaned_data.get('merma_kg')
        if merma_kg is None or merma_kg == '':
            return 0
        return merma_kg
    
class ProduccionHomeView(LoginRequiredMixin, ListView):
    model = Lote
    template_name = 'produccion/home.html'
    context_object_name = 'lotes'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Estadísticas generales
        context['lotes_activos'] = Lote.objects.filter(estado='ACT').count()
        context['producciones_hoy'] = ProduccionDiaria.objects.filter(
            fecha=timezone.now().date()
        ).count()
        
        # Últimos lotes
        context['ultimos_lotes'] = Lote.objects.all().order_by('-fecha_creacion')[:5]
        
        # Producción de la última semana
        fecha_inicio = timezone.now().date() - timedelta(days=7)
        context['produccion_semanal'] = ProduccionDiaria.objects.filter(
            fecha__gte=fecha_inicio
        ).values('fecha').annotate(
            total=Count('id')
        ).order_by('fecha')
        
        # Accesos rápidos para el dashboard
        context['acciones_rapidas'] = [
            {
                'titulo': 'Crear Nuevo Lote',
                'url': 'produccion:lote_create',
                'icono': 'fa-plus-circle',
                'color': 'bg-blue-600',
                'descripcion': 'Iniciar un nuevo lote de producción'
            },
            {
                'titulo': 'Registrar Producción',
                'url': 'produccion:produccion_create',
                'icono': 'fa-industry',
                'color': 'bg-green-600',
                'descripcion': 'Registrar producción diaria'
            },
            {
                'titulo': 'Ver Lotes',
                'url': 'produccion:lote_list',
                'icono': 'fa-list',
                'color': 'bg-purple-600',
                'descripcion': 'Lista completa de lotes'
            },
            {
                'titulo': 'Historial Producción',
                'url': 'produccion:produccion_list',
                'icono': 'fa-history',
                'color': 'bg-yellow-600',
                'descripcion': 'Ver historial de producción'
            }
        ]
        
        return context
