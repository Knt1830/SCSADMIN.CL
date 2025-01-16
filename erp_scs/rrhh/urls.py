from django.urls import path
from . import views

app_name = 'rrhh'

urlpatterns = [
    # Dashboard / Home
    path('', views.home, name='home'),
    
    # Trabajadores
    path('trabajadores/', views.trabajadores, name='trabajadores'),
    path('trabajadores/crear/', views.trabajador_crear, name='trabajador_crear'),
    path('trabajadores/<int:pk>/', views.trabajador_detalle, name='trabajador_detalle'),
    
    # Pagos Mensuales
    path('pagos/mensuales/', views.pagos_mensuales, name='pagos_mensuales'),
    
    # Pagos Temporales
    path('pagos/temporales/', views.pagos_temporales, name='pagos_temporales'),
    
    # Producción Temporal
    path('produccion/temporal/crear/', views.produccion_temporal_crear, name='produccion_temporal_crear'),
    
    # Reportes
    path('reportes/', views.reportes, name='reportes'),
]