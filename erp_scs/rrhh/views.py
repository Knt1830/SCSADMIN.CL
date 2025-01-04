from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from produccion.models import ProduccionDiaria, ItemProduccion
from django.urls import reverse_lazy
from django.db.models import F, Sum
from django.db.models import Q, Sum, Count
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db.models import DecimalField



from .models import Trabajador, TarifaProduccion, ContratoTrabajador
from datetime import datetime, timedelta
from produccion.models import ProduccionDiaria, ItemProduccion
from .forms import TrabajadorForm, TarifaProduccionForm, ContratoTrabajadorForm, ContratoTrabajador

class TrabajadorListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Trabajador
    template_name = 'rrhh/trabajador_list.html'
    context_object_name = 'trabajadores'
    permission_required = 'rrhh.view_trabajador'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        tipo = self.request.GET.get('tipo', '')
        estado = self.request.GET.get('estado', '')

        if search:
            queryset = queryset.filter(
                Q(usuario__first_name__icontains=search) |
                Q(usuario__last_name__icontains=search) |
                Q(rut__icontains=search)
            )
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)
            
        if estado:
            queryset = queryset.filter(estado=estado == 'activo')

        return queryset.select_related('usuario')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipos'] = Trabajador.TIPO_CHOICES
        context['tipo_actual'] = self.request.GET.get('tipo', '')
        context['estado_actual'] = self.request.GET.get('estado', '')
        context['search'] = self.request.GET.get('search', '')
        return context

class TrabajadorCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Trabajador
    form_class = TrabajadorForm
    template_name = 'rrhh/trabajador_form.html'
    success_url = reverse_lazy('rrhh:trabajador_list')
    permission_required = 'rrhh.add_trabajador'

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            messages.error(self.request, f"{field}: {', '.join(errors)}")
        return super().form_invalid(form)

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Trabajador creado exitosamente.')
            return response
        except ValidationError as e:
            messages.error(self.request, e)
            return self.form_invalid(form)

class TrabajadorUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
   model = Trabajador
   form_class = TrabajadorForm
   template_name = 'rrhh/trabajador_form.html'
   success_url = reverse_lazy('rrhh:trabajador_list')
   permission_required = 'rrhh.change_trabajador'

   def form_invalid(self, form):
       for field, errors in form.errors.items():
           messages.error(self.request, f"{field}: {', '.join(errors)}")
       return super().form_invalid(form)

   def form_valid(self, form):
       try:
           response = super().form_valid(form)
           messages.success(self.request, 'Trabajador actualizado exitosamente.')
           return response
       except ValidationError as e:
           messages.error(self.request, e)
           return self.form_invalid(form)

class TrabajadorDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Trabajador
    template_name = 'rrhh/trabajador_detail.html'
    context_object_name = 'trabajador'
    permission_required = 'rrhh.view_trabajador'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trabajador = self.object

        # Información específica según el tipo de trabajador
        if trabajador.tipo == 'TEMPORERO':
            # Obtener tarifas activas
            context['tarifas_activas'] = TarifaProduccion.objects.filter(
                trabajador=trabajador,
                activa=True
            ).select_related('producto')

            # Resumen de producción última semana
            fecha_inicio = timezone.now().date() - timedelta(days=7)
            
            # Calcular producción semanal con totales
            produccion_semanal = ItemProduccion.objects.filter(
                produccion__trabajador=trabajador.usuario,
                produccion__fecha__gte=fecha_inicio
            ).values('produccion__fecha').annotate(
                total_items=Count('id'),
                total_producido=Sum('cantidad_producida'),
                total_pago=Sum(
                    F('cantidad_producida') * F('precio_unidad'),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            ).order_by('-produccion__fecha')
            
            context['produccion_semanal'] = produccion_semanal

        else:  # PLANTA
            # Obtener último contrato activo
            context['contrato_actual'] = ContratoTrabajador.objects.filter(
                trabajador=trabajador,
                activo=True
            ).select_related('trabajador').first()

            # Asistencia última semana
            fecha_inicio = timezone.now().date() - timedelta(days=7)
            context['asistencia_semanal'] = trabajador.asistencias.filter(
                fecha__gte=fecha_inicio
            ).order_by('-fecha')

            # Agregar resumen de horas extra de la semana
            if context['asistencia_semanal'].exists():
                total_horas_extra = context['asistencia_semanal'].aggregate(
                    total=Sum('horas_extra', output_field=DecimalField(max_digits=5, decimal_places=2))
                )
                context['total_horas_extra'] = total_horas_extra['total'] or 0
        
        # Agregar información histórica
        context.update({
            'fecha_antiguedad': (timezone.now().date() - trabajador.fecha_ingreso).days // 365,
            'ultima_actualizacion': trabajador.usuario.date_joined
        })

        return context

class RRHHHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'rrhh/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fecha para filtrar actividades recientes
        fecha_inicio = datetime.now() - timedelta(days=7)
        
        # Estadísticas básicas
        context.update({
            'total_trabajadores': Trabajador.objects.count(),
            'trabajadores_activos': Trabajador.objects.filter(estado=True).count(),
            'liquidaciones_pendientes': 0,  # Se implementará cuando tengamos el modelo
        })

        # Últimas actividades (producciones registradas como ejemplo)
        ultimas_producciones = ProduccionDiaria.objects.filter(
            fecha__gte=fecha_inicio
        ).select_related(
            'trabajador', 
            'lote'
        ).order_by('-fecha', '-hora_inicio')[:5]

        context['ultimas_actividades'] = [{
            'descripcion': f"Producción registrada por {prod.trabajador.get_full_name() if prod.trabajador else 'Usuario desconocido'}",
            'fecha': prod.fecha,
            'url': reverse_lazy('rrhh:produccion_list')
        } for prod in ultimas_producciones]

        return context

class ContratoTrabajadorCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ContratoTrabajador
    form_class = ContratoTrabajadorForm
    template_name = 'rrhh/contrato_create.html'
    permission_required = 'rrhh.add_contratotrabajador'

    def get_success_url(self):
        return reverse_lazy('rrhh:trabajador_detail', kwargs={'pk': self.object.trabajador.pk})

    def get_initial(self):
        initial = super().get_initial()
        initial['trabajador'] = self.kwargs.get('trabajador_pk')
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trabajador = Trabajador.objects.get(pk=self.kwargs.get('trabajador_pk'))
        context['trabajador'] = trabajador
        return context

    def form_valid(self, form):
        form.instance.trabajador_id = self.kwargs.get('trabajador_pk')
        
        # Validar que el trabajador sea de planta
        trabajador = Trabajador.objects.get(pk=self.kwargs.get('trabajador_pk'))
        if trabajador.tipo != 'PLANTA':
            messages.error(self.request, 'Solo se pueden crear contratos para trabajadores de planta.')
            return self.form_invalid(form)
        
        # Desactivar otros contratos activos si este será activo
        if form.instance.activo:
            ContratoTrabajador.objects.filter(
                trabajador=trabajador,
                activo=True
            ).update(activo=False)
            
        messages.success(self.request, 'Contrato creado exitosamente.')
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        # Verificar que el trabajador existe y es de planta
        trabajador = get_object_or_404(Trabajador, pk=self.kwargs.get('trabajador_pk'))
        if trabajador.tipo != 'PLANTA':
            messages.error(request, 'Solo se pueden crear contratos para trabajadores de planta.')
            return redirect('rrhh:trabajador_detail', pk=trabajador.pk)
        return super().dispatch(request, *args, **kwargs)

class ContratoTrabajadorUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ContratoTrabajador
    form_class = ContratoTrabajadorForm
    template_name = 'rrhh/contrato_form.html'
    permission_required = 'rrhh.change_contratotrabajador'

    def get_success_url(self):
        return reverse_lazy('rrhh:trabajador_detail', kwargs={'pk': self.object.trabajador.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trabajador'] = self.object.trabajador
        return context

    def form_valid(self, form):
        # Si se está activando este contrato, desactivar otros
        if form.instance.activo:
            ContratoTrabajador.objects.filter(
                trabajador=form.instance.trabajador,
                activo=True
            ).exclude(pk=form.instance.pk).update(activo=False)
            
        messages.success(self.request, 'Contrato actualizado exitosamente.')
        return super().form_valid(form)

class TarifaProduccionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = TarifaProduccion
    form_class = TarifaProduccionForm
    template_name = 'rrhh/tarifa_create.html'
    permission_required = 'rrhh.add_tarifaproduccion'

    def get_success_url(self):
        return reverse_lazy('rrhh:trabajador_detail', kwargs={'pk': self.kwargs.get('trabajador_pk')})

    def get_initial(self):
        initial = super().get_initial()
        initial['trabajador'] = self.kwargs.get('trabajador_pk')
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trabajador'] = get_object_or_404(Trabajador, pk=self.kwargs.get('trabajador_pk'))
        return context

    def form_valid(self, form):
        form.instance.trabajador_id = self.kwargs.get('trabajador_pk')
        trabajador = get_object_or_404(Trabajador, pk=self.kwargs.get('trabajador_pk'))
        
        if trabajador.tipo != 'TEMPORERO':
            messages.error(self.request, 'Solo se pueden crear tarifas para trabajadores temporeros.')
            return self.form_invalid(form)
            
        if form.instance.activa:
            # Desactivar otras tarifas activas para el mismo producto
            TarifaProduccion.objects.filter(
                trabajador=trabajador,
                producto=form.instance.producto,
                activa=True
            ).update(activa=False)
            
        messages.success(self.request, 'Tarifa creada exitosamente.')
        return super().form_valid(form)

class TarifaProduccionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = TarifaProduccion
    form_class = TarifaProduccionForm
    template_name = 'rrhh/tarifa_form.html'
    permission_required = 'rrhh.change_tarifaproduccion'

    def get_success_url(self):
        return reverse_lazy('rrhh:trabajador_detail', kwargs={'pk': self.object.trabajador.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trabajador'] = self.object.trabajador
        return context

    def form_valid(self, form):
        if form.instance.activa:
            # Desactivar otras tarifas activas para el mismo producto
            TarifaProduccion.objects.filter(
                trabajador=form.instance.trabajador,
                producto=form.instance.producto,
                activa=True
            ).exclude(pk=form.instance.pk).update(activa=False)
            
        messages.success(self.request, 'Tarifa actualizada exitosamente.')
        return super().form_valid(form)

class ProduccionTrabajadorDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Trabajador
    template_name = 'rrhh/produccion_trabajador_detail.html'
    permission_required = 'rrhh.view_trabajador'
    context_object_name = 'trabajador'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trabajador = self.object
        fecha_inicio = self.request.GET.get('fecha_inicio')
        fecha_fin = self.request.GET.get('fecha_fin')

        # Filtrar producciones
        producciones = ProduccionDiaria.objects.filter(trabajador=trabajador.usuario)
        if fecha_inicio:
            producciones = producciones.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            producciones = producciones.filter(fecha__lte=fecha_fin)

        # Calcular totales
        totales = ItemProduccion.objects.filter(
            produccion__in=producciones
        ).aggregate(
            total_unidades=Sum('cantidad_producida'),
            total_pago=Sum(F('cantidad_producida') * F('precio_unidad'))
        )

        context.update({
            'producciones': producciones.order_by('-fecha'),
            'total_unidades': totales['total_unidades'] or 0,
            'total_pago': totales['total_pago'] or 0,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        })

        return context

class LiquidacionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'rrhh/liquidacion_list.html'
    permission_required = 'rrhh.view_liquidacion'
    context_object_name = 'liquidaciones'
    paginate_by = 10

    def get_queryset(self):
        # Placeholder hasta que implementemos el modelo de Liquidación
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fecha_inicio'] = self.request.GET.get('fecha_inicio', '')
        context['fecha_fin'] = self.request.GET.get('fecha_fin', '')
        return context

class LiquidacionCreateView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'rrhh/liquidacion_create.html'
    permission_required = 'rrhh.add_liquidacion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Placeholder hasta que implementemos el modelo de Liquidación
        context['trabajadores'] = Trabajador.objects.filter(estado=True)
        return context

class LiquidacionDetailView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'rrhh/liquidacion_detail.html'
    permission_required = 'rrhh.view_liquidacion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Placeholder hasta que implementemos el modelo de Liquidación
        return context

class ProduccionTrabajadorListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Vista para consultar la producción por trabajador con métricas de productividad"""
    template_name = 'rrhh/produccion_trabajador_list.html'
    context_object_name = 'producciones'
    permission_required = 'rrhh.view_produccion'
    paginate_by = 20

    def get_queryset(self):
        queryset = ProduccionDiaria.objects.all()
        trabajador_id = self.request.GET.get('trabajador')
        fecha_inicio = self.request.GET.get('fecha_inicio')
        fecha_fin = self.request.GET.get('fecha_fin')

        if trabajador_id:
            queryset = queryset.filter(trabajador_id=trabajador_id)
        
        if fecha_inicio:
            queryset = queryset.filter(fecha__gte=fecha_inicio)
        
        if fecha_fin:
            queryset = queryset.filter(fecha__lte=fecha_fin)

        return queryset.select_related(
            'trabajador',
            'trabajador__perfil_trabajador',  # Vuelve a usar esto
            'lote'
        ).prefetch_related(
            'items',
            'items__producto'
        ).order_by('-fecha')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Resto del código existente...

        # Modificar la lógica de cálculo de métricas para manejar los items
        if context['producciones']:
            # Usar una consulta directa de ItemProduccion en lugar de iterar sobre producciones
            items_produccion = ItemProduccion.objects.filter(
                produccion__in=context['producciones']
            ).select_related('producto', 'produccion__trabajador')

            # Métricas por producto
            metricas_producto = items_produccion.values('producto__nombre').annotate(
                total_unidades=Sum('cantidad_producida'),
                total_pago=Sum(F('cantidad_producida') * F('precio_unidad'), 
                            output_field=DecimalField())
            ).order_by('-total_unidades')
            context['metricas_producto'] = metricas_producto

            # Métricas por trabajador
            metricas_trabajador = items_produccion.values(
            'produccion__trabajador__perfil_trabajador__usuario__first_name', 
            'produccion__trabajador__perfil_trabajador__usuario__last_name'
        ).annotate(
            total_unidades=Sum('cantidad_producida'),
            total_pago=Sum(F('cantidad_producida') * F('precio_unidad'), 
                        output_field=DecimalField())
        ).order_by('-total_unidades')
            context['metricas_trabajador'] = metricas_trabajador

        return context

class ContratoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    print("ContratoListView.get_queryset() called") 
    model = ContratoTrabajador
    template_name = 'rrhh/contrato_list.html'
    context_object_name = 'contratos'
    permission_required = 'rrhh.view_contratotrabajador'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        estado = self.request.GET.get('estado', '')
        tipo = self.request.GET.get('tipo', '')

        if search:
            queryset = queryset.filter(
                Q(trabajador__usuario__first_name__icontains=search) |
                Q(trabajador__usuario__last_name__icontains=search) |
                Q(trabajador__rut__icontains=search)
            )
        
        if estado:
            queryset = queryset.filter(activo=estado == 'activo')
            
        if tipo:
            queryset = queryset.filter(tipo_contrato=tipo)

        return queryset.select_related(
            'trabajador',
            'trabajador__usuario'
        ).order_by('-fecha_inicio')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tipos': ContratoTrabajador.TIPO_CONTRATO_CHOICES,
            'tipo_actual': self.request.GET.get('tipo', ''),
            'estado_actual': self.request.GET.get('estado', ''),
            'search': self.request.GET.get('search', ''),
            # Estadísticas
            'total_contratos': ContratoTrabajador.objects.count(),
            'contratos_activos': ContratoTrabajador.objects.filter(activo=True).count(),
            'contratos_indefinidos': ContratoTrabajador.objects.filter(tipo_contrato='INDEFINIDO').count(),
        })
        return context