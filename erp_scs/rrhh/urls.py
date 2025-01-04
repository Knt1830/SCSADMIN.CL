from django.urls import path
from . import views

app_name = 'rrhh'

urlpatterns = [
    # URLs para gestión de trabajadores
    path('', views.RRHHHomeView.as_view(), name='home'),
    path('trabajadores/', views.TrabajadorListView.as_view(), name='trabajador_list'),
    path('trabajadores/crear/', views.TrabajadorCreateView.as_view(), name='trabajador_form'),
    path('trabajadores/<int:pk>/', views.TrabajadorDetailView.as_view(), name='trabajador_detail'),
    path('trabajadores/<int:pk>/editar/', views.TrabajadorUpdateView.as_view(), name='trabajador_update'),
    
    # URLs para contratos (trabajadores de planta)
    path('trabajadores/<int:trabajador_pk>/contratos/crear/', 
         views.ContratoTrabajadorCreateView.as_view(), 
         name='contrato_create'),
    path('trabajadores/<int:trabajador_pk>/contratos/<int:pk>/editar/', 
         views.ContratoTrabajadorUpdateView.as_view(), 
         name='contrato_update'),
    path('contratos/', views.ContratoListView.as_view(), name='contrato_list'),
    
    # URLs para tarifas (trabajadores temporeros)
    path('trabajadores/<int:trabajador_pk>/tarifas/crear/', 
         views.TarifaProduccionCreateView.as_view(), 
         name='tarifa_create'),
    path('trabajadores/<int:trabajador_pk>/tarifas/<int:pk>/editar/', 
         views.TarifaProduccionUpdateView.as_view(), 
         name='tarifa_update'),
    
    # URLs para consulta de producción
    path('produccion/', 
         views.ProduccionTrabajadorListView.as_view(), 
         name='produccion_list'),
    path('produccion/trabajador/<int:trabajador_pk>/', 
         views.ProduccionTrabajadorDetailView.as_view(), 
         name='produccion_detail'),
    path('produccion/trabajadores/', 
          views.ProduccionTrabajadorListView.as_view(), 
          name='produccion_trabajador_list'),
     
    # URLs para liquidaciones
    path('liquidaciones/', 
         views.LiquidacionListView.as_view(), 
         name='liquidacion_list'),
    path('liquidaciones/crear/', 
         views.LiquidacionCreateView.as_view(), 
         name='liquidacion_create'),
    path('liquidaciones/<int:pk>/', 
         views.LiquidacionDetailView.as_view(), 
         name='liquidacion_detail'),
]