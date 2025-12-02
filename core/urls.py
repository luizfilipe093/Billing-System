from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('titulo/<int:id>/', views.detalhe_titulo, name='detalhe_titulo'),
    path('titulo/<int:id>/boleto/', views.boleto_visual, name='boleto_visual'),
    path('titulo/<int:id>/termo/', views.termo_acordo_visual, name='termo_acordo_visual'),
    
    # NOVA ROTA DA RÉGUA:
    path('configuracoes/regua/', views.regua_visual, name='regua_visual'),
]