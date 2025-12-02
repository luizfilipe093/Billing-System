from django.contrib import admin
from .models import Devedor, Titulo, HistoricoContato

@admin.register(Devedor)
class DevedorAdmin(admin.ModelAdmin):
    list_display = ('codigo_externo', 'nome', 'cpf_cnpj', 'cidade', 'uf')
    search_fields = ('nome', 'cpf_cnpj', 'codigo_externo')

@admin.register(Titulo)
class TituloAdmin(admin.ModelAdmin):
    # ADICIONEI 'dias_atraso' e 'valor_atualizado' AQUI
    list_display = ('numero_doc', 'devedor', 'dt_vencimento', 'valor_original', 'dias_atraso', 'valor_atualizado', 'status')
    list_filter = ('status', 'dt_vencimento')
    search_fields = ('numero_doc', 'devedor__nome')

@admin.register(HistoricoContato)
class HistoricoContatoAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'tipo', 'titulo', 'usuario')
    list_filter = ('tipo', 'data_hora')