from django.core.mail import EmailMessage # <--- Mudamos de send_mail para EmailMessage (mais poderoso)
from core.utils import render_to_pdf
from datetime import date
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from core.models import Titulo

class Command(BaseCommand):
    help = 'Motor da Régua de Cobrança (Localiza inadimplentes e simula envio)'

    def handle(self, *args, **options):
        self.stdout.write("=== INICIANDO MOTOR DA RÉGUA ===")
        
        # Trazemos APENAS títulos abertos para não gastar memória à toa
        titulos_abertos = Titulo.objects.filter(status='ABERTO')
        
        cont_email = 0
        cont_sms = 0
        cont_negativacao = 0

        for titulo in titulos_abertos:
            dias = titulo.dias_atraso # Nossa propriedade mágica calculada
            
            # --- REGRA 1: Lembrete Amigável (5 dias) ---
            if dias == 5:
                self.enviar_email_amigavel(titulo)
                cont_email += 1
            
            # --- REGRA 2: Cobrança Incisiva (15 dias) ---
            elif dias == 15:
                self.enviar_sms_cobranca(titulo)
                cont_sms += 1
                
            # --- REGRA 3: Pré-Negativação (30 dias) ---
            elif dias >= 30:
                self.simular_negativacao(titulo)
                cont_negativacao += 1

        self.stdout.write(self.style.SUCCESS(f"\nRESUMO DO PROCESSAMENTO:"))
        self.stdout.write(f"- E-mails enviados (5 dias): {cont_email}")
        self.stdout.write(f"- SMS enviados (15 dias): {cont_sms}")
        self.stdout.write(f"- Negativações (30+ dias): {cont_negativacao}")

    def enviar_email_amigavel(self, titulo):
        assunto = f"Boleto em Atraso: {titulo.numero_doc}"
        
        mensagem = f"""
        Olá {titulo.devedor.nome},
        
        Segue em anexo o boleto atualizado do título {titulo.numero_doc}.
        Vencimento Original: {titulo.dt_vencimento}
        Dias de atraso: {titulo.dias_atraso}
        
        Valor para pagamento hoje: R$ {titulo.valor_atualizado}
        
        Atenciosamente,
        Sua Empresa
        """

        try:
            self.stdout.write(f"Gerando PDF e enviando para {titulo.devedor.email}...")

            # 1. Preparar dados para o PDF (Mesma lógica da View)
            contexto_pdf = {
                't': titulo,
                'data_doc': date.today(),
                'vencimento_novo': date.today(),
                'linha_digitavel': f"00190.50095 40144.816069 06809.350314 3 {titulo.valor_atualizado}".replace('.', '')
            }

            # 2. Gerar o PDF na memória
            pdf_bytes = render_to_pdf('core/boleto_pdf.html', contexto_pdf)
            
            if pdf_bytes:
                # 3. Criar o E-mail com Anexo
                email = EmailMessage(
                    subject=assunto,
                    body=mensagem,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[titulo.devedor.email],
                )
                
                # Anexar: (Nome do Arquivo, Conteúdo, Tipo)
                email.attach(f'boleto_{titulo.numero_doc}.pdf', pdf_bytes, 'application/pdf')
                
                # Enviar
                email.send(fail_silently=False)
                self.stdout.write(self.style.SUCCESS("[OK] E-mail com PDF enviado!"))
            else:
                self.stdout.write(self.style.ERROR("Erro ao gerar PDF."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro: {e}"))

    def enviar_sms_cobranca(self, titulo):
        # Aqui entra a integração com API de SMS (Zenvia, Twilio)
        msg = f"[SMS] Para: {titulo.devedor.telefone} | {titulo.devedor.nome}, evite bloqueio. Pague seu boleto {titulo.numero_doc}."
        print(msg)
        
    def simular_negativacao(self, titulo):
        # Apenas loga, não envia nada por enquanto
        pass