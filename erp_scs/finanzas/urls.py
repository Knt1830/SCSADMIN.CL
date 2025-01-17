from django.urls import path
from . import views

app_name = 'finanzas'

urlpatterns = [
    path('', views.finanzas_home, name='home'),
]