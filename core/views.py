from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Q
from .models import Titulo, Devedor, HistoricoContato, ConfiguracaoFinanceira
from datetime import date, timedelta
import pandas as pd
from django.contrib import messages

from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Q, Count
from django.db.models.functions import TruncDate
from .models import Titulo, Devedor, HistoricoContato
from datetime import date, timedelta

def dashboard(request):
    # --- 1. DADOS GERAIS ---
    total_receber = Titulo.objects.filter(status='ABERTO').aggregate(Sum('saldo_atual'))['saldo_atual__sum'] or 0
    qtd_titulos = Titulo.objects.filter(status='ABERTO').count()
    
    # --- 2. LÓGICA DE PRÓXIMO DA FILA (Para o botão "Realizar Contato") ---
    # Tenta pegar o primeiro título pendente para abrir direto no modal
    proximo_titulo = Titulo.objects.filter(status='ABERTO').order_by('dt_vencimento').first()
    proximo_id = proximo_titulo.id if proximo_titulo else None
    nome_proximo = proximo_titulo.devedor.nome if proximo_titulo else ""

       # --- 3. CÁLCULO DE KPIs (Diário e Mensal) ---
    hoje = date.today()
    inicio_mes = hoje.replace(day=1)
    
    # Filtros de Data
    contatos_hoje_qs = HistoricoContato.objects.filter(data_hora__date=hoje)
    contatos_mes_qs = HistoricoContato.objects.filter(data_hora__date__gte=inicio_mes)
    
    # Totais
    qtd_hoje = contatos_hoje_qs.count()
    qtd_mes = contatos_mes_qs.count()
    
    # "Positivos" (Consideramos acordos ou promessas como positivo para o exemplo)
    # Ajuste a lógica conforme o que você escreve nas anotações
    positivos_hoje = contatos_hoje_qs.filter(Q(anotacao__icontains='acordo') | Q(anotacao__icontains='pago')).count()
    positivos_mes = contatos_mes_qs.filter(Q(anotacao__icontains='acordo') | Q(anotacao__icontains='pago')).count()
    
    # Taxa de Conversão
    taxa_hoje = (positivos_hoje / qtd_hoje * 100) if qtd_hoje > 0 else 0
    taxa_mes = (positivos_mes / qtd_mes * 100) if qtd_mes > 0 else 0
    
    # Agendamentos (Baseado em vencimentos)
    agendados_hoje = Titulo.objects.filter(dt_vencimento=hoje, status='ABERTO').count()
    agendados_amanha = Titulo.objects.filter(dt_vencimento=hoje + timedelta(days=1), status='ABERTO').count()
    agendados_futuros = Titulo.objects.filter(dt_vencimento__gt=hoje + timedelta(days=1), status='ABERTO').count()

    # --- 4. DADOS PARA GRÁFICOS ---
    
    # Mapa de Contatos (Últimos 7 dias)
    data_limite = hoje - timedelta(days=7)
    mapa_contatos = HistoricoContato.objects.filter(data_hora__date__gte=data_limite)\
        .annotate(data_dia=TruncDate('data_hora'))\
        .values('data_dia')\
        .annotate(qtd=Count('id'))\
        .order_by('data_dia')
        
    line_labels = [x['data_dia'].strftime('%d/%m') for x in mapa_contatos]
    line_data = [x['qtd'] for x in mapa_contatos]

    # Tabulação (Tipo de Contato)
    tabulacao = HistoricoContato.objects.values('tipo').annotate(qtd=Count('id'))
    donut_labels = [x['tipo'] for x in tabulacao]
    donut_data = [x['qtd'] for x in tabulacao]

    # Lista para a Tabela (com busca)
    titulos_query = Titulo.objects.filter(status='ABERTO').order_by('dt_vencimento')
    term = request.GET.get('q')
    if term:
        titulos_query = titulos_query.filter(
            Q(devedor__nome__icontains=term) | Q(devedor__cpf_cnpj__icontains=term) | Q(numero_doc__icontains=term)
        )

    return render(request, 'core/dashboard.html', {
        'total_receber': total_receber,
        'qtd_titulos': qtd_titulos,
        'titulos': titulos_query[:20], # Limita a 20 na tabela
        
        # KPIs Calculados
        'qtd_hoje': qtd_hoje, 'positivos_hoje': positivos_hoje, 'taxa_hoje': round(taxa_hoje, 1),
        'qtd_mes': qtd_mes, 'positivos_mes': positivos_mes, 'taxa_mes': round(taxa_mes, 1),
        'agendados_hoje': agendados_hoje, 'agendados_amanha': agendados_amanha, 'agendados_futuros': agendados_futuros,
        
        # Gráficos
        'line_labels': line_labels, 'line_data': line_data,
        'donut_labels': donut_labels, 'donut_data': donut_data,
        
        # Próximo da Fila (Para o botão principal)
        'proximo_id': proximo_id,
        'nome_proximo': nome_proximo,
    })

def detalhe_titulo(request, id):
    titulo = get_object_or_404(Titulo, id=id)
    mensagem = None

    if request.method == 'POST':
        # CENÁRIO A: Salvar Anotação (CRM)
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

        # CENÁRIO B: Atualizar Dados do Cliente (NOVO)
        elif 'btn_atualizar_cliente' in request.POST:
            devedor = titulo.devedor
            devedor.email = request.POST.get('email')
            devedor.telefone = request.POST.get('telefone')
            devedor.pessoa_contato = request.POST.get('pessoa_contato') # Novo Campo
            devedor.logradouro = request.POST.get('logradouro')
            devedor.numero = request.POST.get('numero')
            devedor.bairro = request.POST.get('bairro')
            devedor.cidade = request.POST.get('cidade')
            devedor.uf = request.POST.get('uf')
            devedor.cep = request.POST.get('cep')
            devedor.save()
            
            mensagem = "Dados do cliente atualizados com sucesso!"
            
            # Log automático da alteração
            HistoricoContato.objects.create(
                titulo=titulo,
                usuario=request.user,
                tipo='SISTEMA',
                anotacao="Dados cadastrais atualizados manualmente pelo operador."
            )

        # CENÁRIO C: Confirmar Acordo
        elif 'btn_acordo' in request.POST:
            try:
                entrada = float(request.POST.get('valor_entrada', '0').replace(',', '.'))
                qtd_parcelas = int(request.POST.get('qtd_parcelas', '1'))
            except ValueError:
                entrada = 0.0
                qtd_parcelas = 1

            valor_total = float(titulo.valor_atualizado)
            saldo_restante = valor_total - entrada

            titulo.status = 'ACORDO'
            titulo.save()

            HistoricoContato.objects.create(
                titulo=titulo,
                usuario=request.user,
                tipo='SISTEMA',
                anotacao=f"Acordo realizado. Total: {valor_total}. Entrada: {entrada}. Parcelas: {qtd_parcelas}x."
            )

            if entrada > 0:
                Titulo.objects.create(
                    devedor=titulo.devedor,
                    codigo_titulo_externo=f"{titulo.codigo_titulo_externo}-ENT",
                    numero_doc=f"{titulo.numero_doc}/ENT",
                    dt_vencimento=date.today(),
                    dt_emissao=date.today(),
                    valor_original=entrada,
                    saldo_atual=entrada,
                    status='ABERTO'
                )

            if qtd_parcelas > 0 and saldo_restante > 0:
                valor_parcela = round(saldo_restante / qtd_parcelas, 2)
                for i in range(1, qtd_parcelas + 1):
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

def importar_arquivo_view(request):
    if request.method == 'POST' and request.FILES.get('arquivo_csv'):
        arquivo = request.FILES['arquivo_csv']
        
        try:
            # 1. Leitura com Pandas (Direto da memória)
            try:
                df = pd.read_csv(arquivo, sep=';', encoding='utf-8', dtype=str)
            except UnicodeDecodeError:
                df = pd.read_csv(arquivo, sep=';', encoding='cp1252', dtype=str)
            
            # Limpa nomes das colunas
            df.columns = df.columns.str.strip()
            
            processados = 0
            
            # 2. Processamento (Mesma lógica do Script)
            for index, row in df.iterrows():
                # Tratamento de Datas
                try:
                    dt_venc = datetime.strptime(row['DT_VENCIMENTO'], '%d/%m/%Y').date()
                except:
                    dt_venc = date.today()
                
                try:
                    # Tenta DT_GERACAO ou DT_EMISSAO
                    str_emissao = row.get('DT_GERACAO') or row.get('DT_EMISSAO')
                    dt_emiss = datetime.strptime(str_emissao, '%d/%m/%Y').date()
                except:
                    dt_emiss = date.today()

                # Tratamento de Valores
                val_original_str = row.get('VL_TITULO', '0')
                val_saldo_str = row.get('VL_SALDO', '0')
                val_original = float(str(val_original_str).replace('.', '').replace(',', '.'))
                val_saldo = float(str(val_saldo_str).replace('.', '').replace(',', '.'))

                # Upsert Devedor
                devedor, created = Devedor.objects.get_or_create(
                    codigo_externo=row['COD_DEVEDOR'],
                    defaults={
                        'nome': row['NOME'],
                        'tipo_pessoa': row.get('TP_PESSOA', 'J'),
                        'cpf_cnpj': row.get('CNPJ_CPF', ''),
                        'email': row.get('EMAIL'),
                        'telefone': row.get('FONE 1'),
                        'logradouro': row.get('ENDERECO'),
                        'numero': row.get('NUMERO'),
                        'bairro': row.get('BAIRRO'),
                        'cidade': row.get('CIDADE'),
                        'uf': row.get('ESTADO'),
                        'cep': row.get('CEP')
                    }
                )
                
                # Upsert Título
                # Pega COD_TITULO ou COD_TITULO_SANKHYA
                cod_titulo = row.get('COD_TITULO') or row.get('COD_TITULO_SANKHYA')
                nosso_numero = row.get('NOSSO_NUMERO') or row.get('NUMERO_DOC')

                Titulo.objects.update_or_create(
                    codigo_titulo_externo=cod_titulo,
                    defaults={
                        'devedor': devedor,
                        'numero_doc': nosso_numero,
                        'dt_vencimento': dt_venc,
                        'dt_emissao': dt_emiss,
                        'valor_original': val_original,
                        'saldo_atual': val_saldo,
                        'status': 'ABERTO'
                    }
                )
                processados += 1
            
            messages.success(request, f"Sucesso! {processados} títulos processados/atualizados.")
            
        except Exception as e:
            messages.error(request, f"Erro ao processar arquivo: {str(e)}")

    return render(request, 'core/importar.html')
