from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    path('', views.inventario_home, name='home'),
    path('crear-producto/', views.crear_producto, name='crear_producto'),
    path('consultar-stock/', views.consultar_stock, name='consultar_stock'),
    path('ajuste-inventario/', views.ajuste_inventario, name='ajuste_inventario'),
    path('producto/<int:pk>/', views.detalle_producto, name='detalle_producto'),
    path('movimientos/', views.historial_movimientos, name='historial_movimientos'),
]