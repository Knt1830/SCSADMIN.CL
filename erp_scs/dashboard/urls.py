from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('crear-usuario/', views.crear_usuario, name='crear_usuario'),
    path('perfil/', views.perfil_view, name='perfil'),
]