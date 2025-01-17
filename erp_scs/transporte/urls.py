from django.urls import path
from . import views

app_name = 'transporte'

urlpatterns = [
    # Rutas de inicio
    path('', views.transporte_home, name='home'),

    # Rutas de vehículos
    path('vehiculos/', views.lista_vehiculos, name='lista_vehiculos'),
    path('vehiculo/nuevo/', views.crear_vehiculo, name='crear_vehiculo'),
    path('vehiculo/<int:pk>/', views.detalle_vehiculo, name='detalle_vehiculo'),
    path('vehiculo/<int:pk>/editar/', views.editar_vehiculo, name='editar_vehiculo'),

    # Rutas de choferes
    path('choferes/', views.lista_choferes, name='lista_choferes'),
    path('chofer/nuevo/', views.crear_chofer, name='crear_chofer'),
    path('chofer/<int:pk>/', views.detalle_chofer, name='detalle_chofer'),
    path('chofer/<int:pk>/editar/', views.editar_chofer, name='editar_chofer'),

    # Rutas de gastos de vehículos
    path('gastos/', views.lista_gastos_vehiculo, name='lista_gastos_vehiculo'),
    path('gasto/nuevo/', views.registrar_gasto_vehiculo, name='registrar_gasto_vehiculo'),
    path('gasto/<int:pk>/', views.detalle_gasto_vehiculo, name='detalle_gasto_vehiculo'),
]