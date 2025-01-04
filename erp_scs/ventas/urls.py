# ventas/urls.py
from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    # Página principal de ventas
    path('', views.home_ventas, name='home'),
    
    # Rutas para gestión de clientes
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/registrar/', views.registrar_cliente, name='registrar_cliente'),
    path('clientes/<int:cliente_id>/', views.detalle_cliente, name='detalle_cliente'),
    path('clientes/<int:cliente_id>/editar/', views.editar_cliente, name='editar_cliente'),
    
    # Rutas para gestión de ventas
    path('nueva/', views.nueva_venta, name='nueva_venta'),
    path('ventas/', views.lista_ventas, name='lista_ventas'),
    path('ventas/<int:venta_id>/', views.detalle_venta, name='detalle_venta'),
    path('ventas/<int:venta_id>/editar/', views.editar_venta, name='editar_venta'),
    
    # Rutas para gestión de créditos
    path('creditos/', views.gestionar_creditos, name='gestionar_creditos'),
    path('creditos/<int:credito_id>/pago/', views.registrar_pago_credito, name='registrar_pago_credito'),
]