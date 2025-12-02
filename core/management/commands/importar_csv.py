import pandas as pd
from datetime import datetime
from django.core.management.base import BaseCommand
from core.models import Devedor, Titulo

class Command(BaseCommand):
    help = 'Importa CSV do Sankhya (Layout v3 - Padrão CEDRUS)'

    def add_arguments(self, parser):
        parser.add_argument('arquivo', type=str)

    def handle(self, *args, **options):
        arquivo_path = options['arquivo']
        self.stdout.write(f'Lendo: {arquivo_path}...')

        try:
            # Tenta ler com encoding UTF-8 (Padrão)
            df = pd.read_csv(arquivo_path, sep=';', encoding='utf-8', dtype=str)
        except UnicodeDecodeError:
            self.stdout.write(self.style.WARNING('Tentando encoding Windows-1252...'))
            df = pd.read_csv(arquivo_path, sep=';', encoding='cp1252', dtype=str)

        # Remove espaços dos nomes das colunas (Ex: "FONE 1 " -> "FONE 1")
        df.columns = df.columns.str.strip()
        
        # DEBUG: Mostra as colunas encontradas
        self.stdout.write(f'Colunas detectadas: {list(df.columns)}')

        processados = 0
        erros = 0

        for index, row in df.iterrows():
            try:
                # === 1. TRATAMENTO DE DATAS ===
                # Formato esperado: dd/mm/yyyy
                try:
                    dt_venc = datetime.strptime(row['DT_VENCIMENTO'], '%d/%m/%Y').date()
                except:
                    dt_venc = datetime.today().date() # Fallback se data vier vazia

                try:
                    # No novo CSV a coluna é DT_GERACAO
                    dt_emiss = datetime.strptime(row['DT_GERACAO'], '%d/%m/%Y').date()
                except:
                    dt_emiss = datetime.today().date()

                # === 2. TRATAMENTO DE VALORES ===
                # Converter "1.200,50" -> 1200.50 (Float Python)
                # Se vier vazio, assume 0
                val_original_str = row.get('VL_TITULO', '0')
                val_saldo_str = row.get('VL_SALDO', '0')

                # Replace: tira ponto de milhar e troca vírgula decimal por ponto
                val_original = float(str(val_original_str).replace('.', '').replace(',', '.'))
                val_saldo = float(str(val_saldo_str).replace('.', '').replace(',', '.'))

                # === 3. DEVEDOR (Upsert) ===
                devedor, created = Devedor.objects.get_or_create(
                    codigo_externo=row['COD_DEVEDOR'],
                    defaults={
                        'nome': row['NOME'],
                        'tipo_pessoa': row.get('TP_PESSOA', 'J'),
                        'cpf_cnpj': row['CNPJ_CPF'],
                        'email': row.get('EMAIL'),
                        'telefone': row.get('FONE 1'), # Nome exato do novo CSV
                        'logradouro': row.get('ENDERECO'), # Agora é ENDERECO, não LOGRADOURO
                        'numero': row.get('NUMERO'),
                        'bairro': row.get('BAIRRO'),
                        'cidade': row.get('CIDADE'),
                        'uf': row.get('ESTADO'), # Agora é ESTADO, não UF
                        'cep': row.get('CEP')
                    }
                )

                # Atualiza contato se devedor já existia
                if not created:
                    if row.get('EMAIL'): devedor.email = row.get('EMAIL')
                    if row.get('FONE 1'): devedor.telefone = row.get('FONE 1')
                    devedor.save()

                # === 4. TÍTULO (Upsert) ===
                Titulo.objects.update_or_create(
                    codigo_titulo_externo=row['COD_TITULO'],
                    defaults={
                        'devedor': devedor,
                        'numero_doc': row['NOSSO_NUMERO'], # Novo nome da coluna
                        'dt_vencimento': dt_venc,
                        'dt_emissao': dt_emiss,
                        'valor_original': val_original,
                        'saldo_atual': val_saldo,
                        'status': 'ABERTO'
                    }
                )
                processados += 1

            except Exception as e:
                erros += 1
                self.stdout.write(self.style.ERROR(f'Erro linha {index}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\nProcessamento Finalizado!'))
        self.stdout.write(f'Sucessos: {processados}')
        self.stdout.write(f'Erros: {erros}')