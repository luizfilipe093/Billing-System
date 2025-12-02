from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Q
from .models import Titulo, Devedor, HistoricoContato
from datetime import date

def dashboard(request):
    # 1. KPIs (Indicadores Principais)
    total_receber = Titulo.objects.filter(status='ABERTO').aggregate(Sum('saldo_atual'))['saldo_atual__sum'] or 0
    qtd_titulos = Titulo.objects.filter(status='ABERTO').count()
    qtd_devedores = Devedor.objects.count()

    # 2. A Lista (Tabela)
    # Primeiro criamos a QuerySet base
    titulos_query = Titulo.objects.filter(status='ABERTO').order_by('dt_vencimento')

    # Lógica de Busca
    term = request.GET.get('q')
    
    if term:
        # Filtra: Nome do Devedor OU CPF OU Nosso Número
        titulos_query = titulos_query.filter(
            Q(devedor__nome__icontains=term) | 
            Q(devedor__cpf_cnpj__icontains=term) |
            Q(numero_doc__icontains=term)
        )

    # Paginação: Pegamos os 50 primeiros do resultado final
    ultimos_titulos = titulos_query[:50]

    return render(request, 'core/dashboard.html', {
        'total_receber': total_receber,
        'qtd_titulos': qtd_titulos,
        'qtd_devedores': qtd_devedores,
        'titulos': ultimos_titulos
    }) 

def detalhe_titulo(request, id):
    # Busca o título pelo ID ou dá erro 404 se não achar
    titulo = get_object_or_404(Titulo, id=id)
    mensagem = None

    if request.method == 'POST':
        # CENÁRIO A: Clicou em "Salvar Anotação"
        if 'btn_anotacao' in request.POST:
            texto = request.POST.get('anotacao')
            tipo_contato = request.POST.get('tipo_contato')
            
            if texto:
                HistoricoContato.objects.create(
                    titulo=titulo,
                    usuario=request.user, # Pega o usuário logado (Admin)
                    tipo=tipo_contato,
                    anotacao=texto
                )
        
        # CENÁRIO B: Clicou em "Confirmar Acordo"
        elif 'btn_acordo' in request.POST:
            titulo.status = 'ACORDO'
            titulo.save()
            
            # Registra no histórico automaticamente (Log do Sistema)
            HistoricoContato.objects.create(
                titulo=titulo,
                usuario=request.user,
                tipo='SISTEMA',
                anotacao="Acordo realizado com sucesso através do painel."
            )
            mensagem = "Acordo realizado com sucesso!"

    # Busca o histórico para mostrar na tela
    historico = titulo.historico.all()

    return render(request, 'core/detalhe_titulo.html', {
        't': titulo,
        'mensagem': mensagem,
        'historico': historico
    })

def boleto_visual(request, id):
    titulo = get_object_or_404(Titulo, id=id)
    
    # Lógica de Engenharia:
    # O boleto é gerado para pagamento HOJE (já que está atrasado)
    data_documento = date.today()
    vencimento_novo = date.today() 
    
    # Simulação de Linha Digitável
    linha_digitavel = f"00190.50095 40144.816069 06809.350314 3 {titulo.valor_atualizado}".replace('.', '')

    return render(request, 'core/boleto_impressao.html', {
        't': titulo,
        'data_doc': data_documento,
        'vencimento_novo': vencimento_novo,
        'linha_digitavel': linha_digitavel
    })