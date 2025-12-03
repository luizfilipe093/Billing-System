from django.db import models
from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Devedor(models.Model):
    codigo_externo = models.CharField("Cód. Devedor", max_length=50, unique=True)
    nome = models.CharField(max_length=255)
    tipo_pessoa = models.CharField("Tipo Pessoa", max_length=20, null=True, blank=True)
    cpf_cnpj = models.CharField("CPF/CNPJ", max_length=20, null=True, blank=True)
    pessoa_contato = models.CharField("Pessoa de Contato", max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    telefone = models.CharField(max_length=50, null=True, blank=True)
    logradouro = models.CharField(max_length=255, null=True, blank=True)
    numero = models.CharField(max_length=50, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    uf = models.CharField(max_length=2, null=True, blank=True)
    cep = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.nome} ({self.codigo_externo})"

class ConfiguracaoFinanceira(models.Model):
    multa_percentual = models.DecimalField(
        "Multa (%) por Atraso",
        max_digits=5,
        decimal_places=2,
        default=Decimal('2.00'),
        help_text="Valor percentual da multa (ex: 2.00 para 2%)."
    )
    juros_mensal_percentual = models.DecimalField(
        "Juros (%) ao Mês",
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text="Valor percentual dos juros ao mês (ex: 1.00 para 1%)."
    )

    class Meta:
        verbose_name = "Configuração Financeira"
        verbose_name_plural = "Configurações Financeiras"

    # Garante que só haja um registro (Singleton Pattern)
    def clean(self):
        if ConfiguracaoFinanceira.objects.exists() and self.pk is None:
            raise ValidationError("Só pode existir uma configuração financeira.")
        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return "Regras Ativas do Sistema"

class Titulo(models.Model):
    STATUS_CHOICES = [
        ('ABERTO', 'Em Aberto'),
        ('ACORDO', 'Em Acordo'),
        ('PAGO', 'Pago'),
    ]

    devedor = models.ForeignKey(Devedor, on_delete=models.CASCADE, related_name='titulos')
    codigo_titulo_externo = models.CharField("Cód. Título", max_length=50, unique=True)
    numero_doc = models.CharField("Nosso Número", max_length=50)
    dt_vencimento = models.DateField("Vencimento")
    dt_emissao = models.DateField("Emissão")
    valor_original = models.DecimalField("Valor Original", max_digits=15, decimal_places=2)
    saldo_atual = models.DecimalField("Saldo Importado", max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTO')

    def __str__(self):
        return f"Doc: {self.numero_doc} - R$ {self.valor_original}"

    @property
    def dias_atraso(self):
        """Retorna quantos dias o título está vencido"""
        if self.status != 'ABERTO':
            return 0
        hoje = date.today()
        if hoje > self.dt_vencimento:
            delta = hoje - self.dt_vencimento
            return delta.days
        return 0

    @property
    def valor_atualizado(self):
        """Calcula o Valor Atualizado lendo as regras da Configuração."""
        if self.dias_atraso <= 0:
            return self.valor_original

        # 1. Busca as regras ativas no banco (Singleton)
        try:
            regras = ConfiguracaoFinanceira.objects.first()
        except:
            # Fallback seguro caso o banco ainda não tenha sido populado/migrado
            # Usa valores padrão: Multa 2% e Juros 1%
            multa_taxa = Decimal('0.02')
            juros_taxa_diaria = (Decimal('1.00') / 100) / 30
        else:
            if regras:
                multa_taxa = regras.multa_percentual / 100
                juros_taxa_diaria = (regras.juros_mensal_percentual / 100) / 30
            else:
                 multa_taxa = Decimal('0.02')
                 juros_taxa_diaria = (Decimal('1.00') / 100) / 30
        
        # Aplica o cálculo
        multa = self.valor_original * multa_taxa
        juros = self.valor_original * juros_taxa_diaria * self.dias_atraso

        total = self.valor_original + multa + juros
        return round(total, 2)

class HistoricoContato(models.Model):
    TIPO_CHOICES = [
        ('LIGACAO', '📞 Ligação'),
        ('WHATSAPP', '📱 WhatsApp'),
        ('EMAIL', '📧 E-mail'),
        ('SISTEMA', '⚙️ Sistema'),
    ]

    titulo = models.ForeignKey(Titulo, on_delete=models.CASCADE, related_name='historico')
    data_hora = models.DateTimeField(auto_now_add=True) # Data automática
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True) # Quem anotou
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='LIGACAO')
    anotacao = models.TextField("Anotação")

    class Meta:
        ordering = ['-data_hora'] # Mais recentes primeiro

    def __str__(self):
        return f"{self.get_tipo_display()} em {self.data_hora}"
