from django.urls import path
from . import views

app_name = 'produccion'

urlpatterns = [
    # Gestión de Lotes
    path('lotes/', views.LoteListView.as_view(), name='lote_list'),
    path('lotes/crear/', views.LoteCreateView.as_view(), name='lote_create'),
    path('lotes/<int:pk>/', views.LoteDetailView.as_view(), name='lote_detail'),
    path('lotes/<int:pk>/editar/', views.LoteUpdateView.as_view(), name='lote_update'),
    
    # Gestión de Producción
    path('produccion/', views.ProduccionListView.as_view(), name='produccion_list'),
    path('produccion/crear/', views.ProduccionCreateView.as_view(), name='produccion_create'),

    path('', views.ProduccionHomeView.as_view(), name='home'),
]