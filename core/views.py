from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Q
from .models import Titulo, Devedor, HistoricoContato, ConfiguracaoFinanceira
from datetime import date, timedelta

def dashboard(request):
    # 1. KPIs
    total_receber = Titulo.objects.filter(status='ABERTO').aggregate(Sum('saldo_atual'))['saldo_atual__sum'] or 0
    qtd_titulos = Titulo.objects.filter(status='ABERTO').count()
    qtd_devedores = Devedor.objects.count()

    # 2. Lista Base
    titulos_query = Titulo.objects.filter(status='ABERTO').order_by('dt_vencimento')

    # Lógica de Busca
    term = request.GET.get('q')
    status_filtro = request.GET.get('status', 'ABERTO')

    # Filtro de Status
    if status_filtro != 'TUDO':
        titulos_query = Titulo.objects.filter(status=status_filtro).order_by('dt_vencimento')
    else:
        titulos_query = Titulo.objects.all().order_by('dt_vencimento')

    # Filtro de Texto
    if term:
        titulos_query = titulos_query.filter(
            Q(devedor__nome__icontains=term) |
            Q(devedor__cpf_cnpj__icontains=term) |
            Q(numero_doc__icontains=term)
        )

    # 3. BI Logic (Faixas de Atraso)
    hoje = date.today()
    query_vencidos = titulos_query.filter(status='ABERTO', dt_vencimento__lt=hoje)
    
    faixas_dados = {
        '0_30': query_vencidos.filter(dt_vencimento__gte=hoje - timedelta(days=30)).count(),
        '31_60': query_vencidos.filter(dt_vencimento__lt=hoje - timedelta(days=30), dt_vencimento__gte=hoje - timedelta(days=60)).count(),
        '61_90': query_vencidos.filter(dt_vencimento__lt=hoje - timedelta(days=60), dt_vencimento__gte=hoje - timedelta(days=90)).count(),
        '90_MAIS': query_vencidos.filter(dt_vencimento__lt=hoje - timedelta(days=90)).count(),
    }

    # Paginação
    ultimos_titulos = titulos_query[:50]

    return render(request, 'core/dashboard.html', {
        'total_receber': total_receber,
        'qtd_titulos': qtd_titulos,
        'qtd_devedores': qtd_devedores,
        'titulos': ultimos_titulos,
        'faixas_dados': faixas_dados,
        'status_selecionado': status_filtro,
    })

def detalhe_titulo(request, id):
    titulo = get_object_or_404(Titulo, id=id)
    mensagem = None

    if request.method == 'POST':
        # CENÁRIO A: Salvar Anotação
        if 'btn_anotacao' in request.POST:
            texto = request.POST.get('anotacao')
            tipo_contato = request.POST.get('tipo_contato')
            
            if texto:
                HistoricoContato.objects.create(
                    titulo=titulo,
                    usuario=request.user,
                    tipo=tipo_contato,
                    anotacao=texto
                )

        # CENÁRIO B: Confirmar Acordo (COM PARCELAMENTO)
        elif 'btn_acordo' in request.POST:
            # 1. Ler dados do formulário
            try:
                entrada = float(request.POST.get('valor_entrada', '0').replace(',', '.'))
                qtd_parcelas = int(request.POST.get('qtd_parcelas', '1'))
            except ValueError:
                entrada = 0.0
                qtd_parcelas = 1

            valor_total = float(titulo.valor_atualizado)
            saldo_restante = valor_total - entrada

            # 2. Baixa o Título Original (Pai)
            titulo.status = 'ACORDO'
            titulo.save()

            # Log do Sistema
            HistoricoContato.objects.create(
                titulo=titulo,
                usuario=request.user,
                tipo='SISTEMA',
                anotacao=f"Acordo realizado. Total: {valor_total}. Entrada: {entrada}. Parcelas: {qtd_parcelas}x."
            )

            # 3. Gerar Título da Entrada (Se houver)
            if entrada > 0:
                Titulo.objects.create(
                    devedor=titulo.devedor,
                    codigo_titulo_externo=f"{titulo.codigo_titulo_externo}-ENT",
                    numero_doc=f"{titulo.numero_doc}/ENT",
                    dt_vencimento=date.today(), # Vence hoje
                    dt_emissao=date.today(),
                    valor_original=entrada,
                    saldo_atual=entrada,
                    status='ABERTO'
                )

            # 4. Gerar Títulos das Parcelas
            if qtd_parcelas > 0 and saldo_restante > 0:
                valor_parcela = round(saldo_restante / qtd_parcelas, 2)

                for i in range(1, qtd_parcelas + 1):
                    # Vencimento: Hoje + 30 dias * número da parcela
                    novo_vencimento = date.today() + timedelta(days=30 * i)
                    
                    Titulo.objects.create(
                        devedor=titulo.devedor,
                        codigo_titulo_externo=f"{titulo.codigo_titulo_externo}-{i}",
                        numero_doc=f"{titulo.numero_doc}/{i}",
                        dt_vencimento=novo_vencimento,
                        dt_emissao=date.today(),
                        valor_original=valor_parcela,
                        saldo_atual=valor_parcela,
                        status='ABERTO'
                    )

            mensagem = "Acordo realizado! Novos boletos foram gerados."

    historico = titulo.historico.all()

    return render(request, 'core/detalhe_titulo.html', {
        't': titulo,
        'mensagem': mensagem,
        'historico': historico
    })

def boleto_visual(request, id):
    titulo = get_object_or_404(Titulo, id=id)
    data_documento = date.today()
    vencimento_novo = date.today()
    linha_digitavel = f"00190.50095 40144.816069 06809.350314 3 {titulo.valor_atualizado}".replace('.', '')

    return render(request, 'core/boleto_impressao.html', {
        't': titulo,
        'data_doc': data_documento,
        'vencimento_novo': vencimento_novo,
        'linha_digitavel': linha_digitavel
    })

def termo_acordo_visual(request, id):
    titulo = get_object_or_404(Titulo, id=id)
    contexto = {
        't': titulo,
        'data_atual': date.today(),
        'empresa_nome': 'SUA EMPRESA LTDA',
        'empresa_cnpj': '00.000.000/0001-00',
        'valor_extenso': 'valor a ser preenchido',
    }
    return render(request, 'core/termo_acordo_pdf.html', contexto)

def regua_visual(request):
    return render(request, 'core/regua_cobranca.html')