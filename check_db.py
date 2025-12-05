import os
import django
from django.conf import settings
from datetime import date, timedelta
from django.db.models import Sum

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print(f"DB Engine: {settings.DATABASES['default']['ENGINE']}")

try:
    from core.models import Titulo
    
    hoje = date.today()
    print(f"Data de Hoje: {hoje}")
    
    titulos_abertos = Titulo.objects.filter(status='ABERTO')
    print(f"Titulos Abertos: {titulos_abertos.count()}")
    
    # Faixas de datas
    d30 = hoje - timedelta(days=30)
    d60 = hoje - timedelta(days=60)
    d90 = hoje - timedelta(days=90)

    # Cálculos dos buckets
    v_a_vencer = titulos_abertos.filter(dt_vencimento__gte=hoje).aggregate(Sum('saldo_atual'))['saldo_atual__sum'] or 0
    v_30_dias  = titulos_abertos.filter(dt_vencimento__lt=hoje, dt_vencimento__gte=d30).aggregate(Sum('saldo_atual'))['saldo_atual__sum'] or 0
    v_60_dias  = titulos_abertos.filter(dt_vencimento__lt=d30, dt_vencimento__gte=d60).aggregate(Sum('saldo_atual'))['saldo_atual__sum'] or 0
    v_90_dias  = titulos_abertos.filter(dt_vencimento__lt=d60, dt_vencimento__gte=d90).aggregate(Sum('saldo_atual'))['saldo_atual__sum'] or 0
    v_90_plus  = titulos_abertos.filter(dt_vencimento__lt=d90).aggregate(Sum('saldo_atual'))['saldo_atual__sum'] or 0

    aging_data = [float(v_a_vencer), float(v_30_dias), float(v_60_dias), float(v_90_dias), float(v_90_plus)]
    print(f"Aging Data: {aging_data}")
    
    # Print sample details
    print("\nDetalhes (Amostra):")
    for t in titulos_abertos[:5]:
        print(f" - {t.numero_doc}: Vencimento {t.dt_vencimento}, Saldo: {t.saldo_atual}")

except Exception as e:
    print(f"Error: {e}")
