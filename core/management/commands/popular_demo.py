from django.core.management.base import BaseCommand
from core.models import Devedor, Titulo, HistoricoContato
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados cenográficos para a apresentação (Aging List calibrado)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("--- INICIANDO CENOGRAFIA PARA O 'DIA D' ---"))
        
        # 1. LIMPEZA CIRÚRGICA
        # Removemos apenas os dados da demo para não duplicar se rodar 2 vezes
        nomes_demo = ["Transportadora Veloz S.A.", "Supermercado Aliança", "Farmácia Saúde Total", "Oficina do Pedro"]
        Devedor.objects.filter(nome__in=nomes_demo).delete()
        self.stdout.write("[OK] Dados antigos da demo removidos.")

        # 2. CRIANDO OS ATORES (DEVEDORES)
        
        # A) O Caso Crítico (Para o Alerta Vermelho)
        transportadora = Devedor.objects.create(
            codigo_externo="DEMO-01",
            nome="Transportadora Veloz S.A.",
            tipo_pessoa="J",
            cpf_cnpj="12.345.678/0001-99",
            email="financeiro@veloz.com.br",
            telefone="(11) 99999-1234",
            cidade="São Paulo",
            uf="SP",
            logradouro="Rodovia Anhanguera, km 15"
        )

        # B) O Caso Médio (Para Negociação)
        mercado = Devedor.objects.create(
            codigo_externo="DEMO-02",
            nome="Supermercado Aliança",
            tipo_pessoa="J",
            cpf_cnpj="98.765.432/0001-11",
            email="compras@alianca.com",
            telefone="(21) 98888-5678",
            cidade="Rio de Janeiro",
            uf="RJ",
            logradouro="Av. Atlântica, 1500"
        )

        # C) O Caso Recente
        oficina = Devedor.objects.create(
            codigo_externo="DEMO-03",
            nome="Oficina do Pedro",
            tipo_pessoa="F",
            cpf_cnpj="123.456.789-00",
            telefone="(31) 97777-4444",
            cidade="Belo Horizonte",
            uf="MG",
            logradouro="Rua das Chaves, 40"
        )

        # D) O Bom Pagador
        farmacia = Devedor.objects.create(
            codigo_externo="DEMO-04",
            nome="Farmácia Saúde Total",
            tipo_pessoa="J",
            cpf_cnpj="11.222.333/0001-00",
            telefone="(41) 3333-2222",
            cidade="Curitiba",
            uf="PR",
            logradouro="Rua das Flores, 100"
        )

        self.stdout.write("[OK] Devedores criados.")

        # 3. INJETANDO TÍTULOS (A MÁGICA DO AGING)
        # Aqui definimos datas exatas para cair em cada faixa do gráfico
        hoje = date.today()

        # FAIXA VERMELHA (> 90 dias)
        # Vencido há 120 dias
        Titulo.objects.create(
            devedor=transportadora,
            codigo_titulo_externo="TIT-VELOZ-01",
            numero_doc="NF-1001",
            dt_emissao=hoje - timedelta(days=150),
            dt_vencimento=hoje - timedelta(days=120), 
            valor_original=15000.00,
            saldo_atual=15000.00, 
            status='ABERTO'
        )
        # Adiciona um histórico para o gráfico de linha não ficar vazio
        HistoricoContato.objects.create(
            titulo=Titulo.objects.get(codigo_titulo_externo="TIT-VELOZ-01"),
            data_hora=hoje - timedelta(days=5),
            tipo="EMAIL",
            anotacao="Cobrança automática enviada. Cliente visualizou mas não respondeu."
        )

        # FAIXA AMARELA (30 a 60 dias)
        # Vencido há 45 dias
        Titulo.objects.create(
            devedor=mercado,
            codigo_titulo_externo="TIT-MERCADO-01",
            numero_doc="NF-2050",
            dt_emissao=hoje - timedelta(days=60),
            dt_vencimento=hoje - timedelta(days=45),
            valor_original=5500.00,
            saldo_atual=5500.00,
            status='ABERTO'
        )

        # FAIXA AZUL (Até 30 dias)
        # Vencido há 10 dias
        Titulo.objects.create(
            devedor=oficina,
            codigo_titulo_externo="TIT-OFICINA-01",
            numero_doc="NF-3005",
            dt_emissao=hoje - timedelta(days=20),
            dt_vencimento=hoje - timedelta(days=10),
            valor_original=1200.00,
            saldo_atual=1200.00,
            status='ABERTO'
        )

        # FAIXA VERDE (A Vencer)
        # Vence daqui a 5 dias
        Titulo.objects.create(
            devedor=farmacia,
            codigo_titulo_externo="TIT-FARMA-01",
            numero_doc="NF-4000",
            dt_emissao=hoje - timedelta(days=5),
            dt_vencimento=hoje + timedelta(days=5),
            valor_original=8000.00,
            saldo_atual=8000.00,
            status='ABERTO'
        )

        self.stdout.write(self.style.SUCCESS("--- SUCESSO! DADOS DO 'DIA D' INJETADOS ---"))
        self.stdout.write(self.style.SUCCESS("ATENCAO: De F5 no Dashboard para ver o grafico colorido."))
