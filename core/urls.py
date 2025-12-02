from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('titulo/<int:id>/', views.detalhe_titulo, name='detalhe_titulo'),
    # NOVA ROTA:
    path('titulo/<int:id>/boleto/', views.boleto_visual, name='boleto_visual'),
]