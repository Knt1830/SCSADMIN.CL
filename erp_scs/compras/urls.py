# compras/urls.py
from django.urls import path
from . import views

app_name = 'compras'

urlpatterns = [
    # Páginas principales
    path('', views.compras_home, name='home'),
    
    # Gestión de proveedores
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/crear/', views.crear_proveedor, name='crear_proveedor'),
    path('proveedores/<int:pk>/', views.detalle_proveedor, name='detalle_proveedor'),
    path('proveedores/<int:pk>/editar/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/<int:pk>/eliminar/', views.eliminar_proveedor, name='eliminar_proveedor'),
    
    # Gestión de tipos de proveedor
    path('tipos-proveedor/', views.lista_tipos_proveedor, name='lista_tipos_proveedor'),
    path('tipos-proveedor/crear/', views.crear_tipo_proveedor, name='crear_tipo_proveedor'),
    path('tipos-proveedor/<int:pk>/editar/', views.editar_tipo_proveedor, name='editar_tipo_proveedor'),
    
    # Órdenes de compra
    path('ordenes/', views.lista_ordenes, name='lista_ordenes'),
    path('ordenes/crear/', views.crear_orden, name='crear_orden'),
    path('ordenes/<int:pk>/', views.detalle_orden, name='detalle_orden'),
    path('ordenes/<int:pk>/editar/', views.editar_orden, name='editar_orden'),
    path('orden/<int:pk>/actualizar-estado/', views.actualizar_estado_orden, name='actualizar_estado_orden'),
    
   
]