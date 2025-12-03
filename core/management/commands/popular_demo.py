from django.core.management.base import BaseCommand
from core.models import Devedor, Titulo, HistoricoContato
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Cria dados de cinema para a apresentação (Cenografia)'

    def handle(self, *args, **options):
        self.stdout.write("🎬 Iniciando Cenografia para a Demo...")

        # Nota: Não vamos apagar seus dados reais. Vamos apenas ADICIONAR estes casos.
        # Eles terão códigos 'DEMO' para você identificar fácil.

        # ---------------------------------------------------------
        # CASO 1: O CRÍTICO (Para mostrar o Gráfico Vermelho e Alerta)
        # ---------------------------------------------------------
        dev1, _ = Devedor.objects.get_or_create(
            codigo_externo='DEMO-001',
            defaults={
                'nome': 'TRANSPORTADORA VELOZ LTDA',
                'cpf_cnpj': '12.345.678/0001-99',
                'email': 'financeiro@veloz.com.br',
                'telefone': '(11) 99999-1111',
                'logradouro': 'Rodovia Anhanguera, KM 30',
                'numero': 'S/N',
                'bairro': 'Industrial',
                'cidade': 'São Paulo', 'uf': 'SP', 'cep': '05000-000'
            }
        )
        
        # Título de 45 mil, vencido há 95 dias (Barra Vermelha no BI)
        Titulo.objects.get_or_create(
            codigo_titulo_externo='TIT-CRI-001',
            defaults={
                'devedor': dev1,
                'numero_doc': 'NF-5501',
                'dt_vencimento': date.today() - timedelta(days=95), 
                'dt_emissao': date.today() - timedelta(days=120),
                'valor_original': 45000.00,
                'saldo_atual': 45000.00,
                'status': 'ABERTO'
            }
        )
        self.stdout.write(self.style.ERROR(f"🔴 Criado caso Crítico (95 dias): {dev1.nome}"))

        # ---------------------------------------------------------
        # CASO 2: A NEGOCIAÇÃO (Para você operar ao vivo)
        # ---------------------------------------------------------
        dev2, _ = Devedor.objects.get_or_create(
            codigo_externo='DEMO-002',
            defaults={
                'nome': 'SUPERMERCADO ALIANÇA S.A.',
                'cpf_cnpj': '98.765.432/0001-00',
                'email': 'contas@alianca.com.br', 
                'telefone': '(11) 98888-2222',
                'logradouro': 'Av. das Nações',
                'numero': '1000',
                'bairro': 'Centro',
                'cidade': 'Campinas', 'uf': 'SP', 'cep': '13000-000'
            }
        )
        
        # Título de 5.200, vencido há 15 dias (Ideal para simular parcelamento)
        t2, _ = Titulo.objects.get_or_create(
            codigo_titulo_externo='TIT-NEG-001',
            defaults={
                'devedor': dev2,
                'numero_doc': 'NF-1020',
                'dt_vencimento': date.today() - timedelta(days=15),
                'dt_emissao': date.today() - timedelta(days=45),
                'valor_original': 5200.00,
                'saldo_atual': 5200.00,
                'status': 'ABERTO'
            }
        )
        
        # Adiciona um histórico para dar contexto na tela
        if not HistoricoContato.objects.filter(titulo=t2).exists():
            HistoricoContato.objects.create(
                titulo=t2,
                tipo='LIGACAO',
                anotacao="Cliente atendeu. Alegou problema de fluxo de caixa. Pediu para retornar hoje com proposta de parcelamento.",
                usuario=None # Sistema
            )
        self.stdout.write(self.style.WARNING(f"🟡 Criado caso Negociação (15 dias): {dev2.nome}"))

        # ---------------------------------------------------------
        # CASO 3: O SUCESSO (Para mostrar KPIs verdes e Acordos)
        # ---------------------------------------------------------
        dev3, _ = Devedor.objects.get_or_create(
            codigo_externo='DEMO-003',
            defaults={
                'nome': 'FARMÁCIA SAÚDE TOTAL',
                'cpf_cnpj': '11.111.111/0001-11',
                'email': 'pagar@saude.com',
                'telefone': '(11) 97777-3333',
                'logradouro': 'Rua da Saúde',
                'numero': '10',
                'bairro': 'Jardim',
                'cidade': 'Jundiaí', 'uf': 'SP', 'cep': '13200-000'
            }
        )
        
        # Título original que já foi negociado
        Titulo.objects.get_or_create(
            codigo_titulo_externo='TIT-SUC-001',
            defaults={
                'devedor': dev3,
                'numero_doc': 'NF-0033',
                'dt_vencimento': date.today() - timedelta(days=60),
                'dt_emissao': date.today() - timedelta(days=90),
                'valor_original': 2500.00,
                'saldo_atual': 0.00, 
                'status': 'ACORDO' # Já aparece como resolvido
            }
        )
        
        # Cria o boleto da entrada (que foi gerado no acordo)
        Titulo.objects.get_or_create(
            codigo_titulo_externo='TIT-SUC-ENT',
            defaults={
                'devedor': dev3,
                'numero_doc': 'NF-0033/ENT',
                'dt_vencimento': date.today(),
                'dt_emissao': date.today(),
                'valor_original': 500.00,
                'saldo_atual': 500.00,
                'status': 'ABERTO'
            }
        )
        
        self.stdout.write(self.style.SUCCESS(f"🟢 Criado caso Sucesso (Acordo): {dev3.nome}"))
        self.stdout.write("\n🎬 CENÁRIO PRONTO! Boa sorte na apresentação.")