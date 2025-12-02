from django.db import models
from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User

class Devedor(models.Model):
    codigo_externo = models.CharField("Cód. Devedor", max_length=50, unique=True)
    nome = models.CharField(max_length=255)
    tipo_pessoa = models.CharField("Tipo Pessoa", max_length=20, null=True, blank=True)
    cpf_cnpj = models.CharField("CPF/CNPJ", max_length=20, null=True, blank=True)
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

    # === A MÁGICA DA ENGENHARIA COMEÇA AQUI ===

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
        """Calcula: Valor + Multa (2%) + Juros (0.033% ao dia = 1% ao mês)"""
        if self.dias_atraso <= 0:
            return self.valor_original
        
        # Multa de 2%
        multa = self.valor_original * Decimal('0.02')
        
        # Juros Simples (0.0333% ao dia)
        taxa_juros_dia = Decimal('0.01') / 30 
        juros = self.valor_original * taxa_juros_dia * self.dias_atraso
        
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