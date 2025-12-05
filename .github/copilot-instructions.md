# AI Coding Agent Instructions - Sistema de Cobrança Django

## Architecture Overview

This is a **Django 5.2 billing collection management system** (`sistema-cobranca-django`) for tracking and managing overdue accounts receivable with automated collection workflows.

### Core Components

**Data Model** (`core/models.py`):
- **Devedor** (Debtor): External entity with contact info, address, CPF/CNPJ
- **Titulo** (Bill/Invoice): Individual receivables tied to Debtors with financial calculations
- **ConfiguracaoFinanceira**: Singleton configuration for system-wide interest rates and penalties
- **HistoricoContato** (Contact History): CRM audit trail linked to Bills, recording all interactions (calls, WhatsApp, email)

**Key Property**: `Titulo.valor_atualizado` (computed property) dynamically calculates bill value including penalties and daily interest based on `dias_atraso` and `ConfiguracaoFinanceira` rules.

### Data Flow

1. **Import Phase**: CSV files (Sankhya/CEDRUS format) → `importar_arquivo_view()` or `importar_csv` management command
2. **Dashboard**: Aggregates open bills into aging buckets (0-30, 30-60, 60-90, 90+ days) with contact KPIs
3. **Collection Workflow**: User navigates bills → updates debtor contact info → records interactions → confirms agreements
4. **Agreements**: Converts single overdue bill into structured payment plan (entry + N installments as new bills)

## Critical Developer Workflows

### Local Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver

# Populate demo data (optional)
python manage.py popular_demo
```

### CSV Import (Primary Data Entry)
```bash
# Command-line import
python manage.py importar_csv <path-to-csv>

# Web UI import
# Navigate to `/importar/` → Upload CSV → Auto-process records
```

**CSV Format Expectations** (Sankhya/CEDRUS):
- Semicolon-separated (`;`)
- Expected columns: `COD_DEVEDOR`, `NOME`, `CNPJ_CPF`, `DT_VENCIMENTO`, `DT_GERACAO`, `VL_TITULO`, `VL_SALDO`, `ENDERECO`, `EMAIL`, `FONE 1`, `ESTADO`, `CEP`
- Date format: `DD/MM/YYYY`
- Currency format: `1.200,50` (dot thousands, comma decimal)
- Encodings: UTF-8 preferred, auto-fallback to Windows-1252 (cp1252)

### Processing Rules Engine
```bash
# Automated collection workflow (runs independently)
python manage.py processar_regua
```

Executes business rules based on `dias_atraso`:
- **Day 5**: Friendly reminder email
- **Day 15**: Urgent SMS collection notice
- **Day 30+**: Pre-negativation (default collection agency notification)

### Docker Deployment
```bash
docker-compose up --build
# Runs on http://0.0.0.0:8000 with PostgreSQL backend via .env
```

## Project-Specific Patterns & Conventions

### Model Conventions

1. **Upsert Pattern** (Django ORM):
   ```python
   # Used consistently in imports to merge duplicate external records
   obj, created = Model.objects.get_or_create(
       codigo_externo=external_id,
       defaults={...}
   )
   # or
   Model.objects.update_or_create(codigo_externo=..., defaults={...})
   ```

2. **Singleton Configuration**:
   `ConfiguracaoFinanceira` enforces single record via `clean()` method with `ValidationError`. Always fetch via `.first()` with fallback defaults (2% penalty, 1% monthly interest).

3. **Decimal Precision**: All financial values use `DecimalField(max_digits=15, decimal_places=2)` to avoid float rounding errors.

### View Conventions

1. **Form-Based CRM** (`detalhe_titulo`):
   - Multi-action POST handler with button-name detection: `btn_anotacao`, `btn_atualizar_cliente`, `btn_acordo`
   - Each action creates `HistoricoContato` audit record
   - No API endpoints; all interactions via HTML forms

2. **Agreement Generation**:
   - Converts single bill → status='ACORDO' → creates new `Titulo` objects for entry (today) + installments (30-day intervals)
   - Suffix convention: `-ENT` (entry), `-1`, `-2`, etc. (installments)

### CSV Handling Patterns

- **Flexible column mapping**: Code handles multiple column names (e.g., `DT_GERACAO` OR `DT_EMISSAO`, `ENDERECO` OR `LOGRADOURO`, `ESTADO` OR `UF`)
- **Type coercion**: All CSV reads use `dtype=str` then parse dates/decimals to prevent inference errors
- **Currency normalization**: `str.replace('.', '').replace(',', '.')` for Brazilian format conversion

### PDF Generation

`core/utils.py` provides `render_to_pdf()` helper:
- Takes Django template path + context dict
- Returns bytes (in-memory PDF via xhtml2pdf/pisa)
- Used for boleto and agreement PDFs (`boleto_impressao.html`, `termo_acordo_pdf.html`)

### Dashboard Aggregation Query Pattern

Uses `annotate()` + `aggregate()` for efficient bulk calculations:
```python
# Aging buckets with date filtering
v_30_dias = titulos_abertos.filter(
    dt_vencimento__lt=hoje, 
    dt_vencimento__gte=d30
).aggregate(Sum('saldo_atual'))['saldo_atual__sum'] or 0
```

## Integration Points & External Dependencies

### Key Libraries

| Library | Purpose | Usage Example |
|---------|---------|---|
| **Django 5.2** | Web framework | Models, views, ORM, admin, migrations |
| **pandas** | CSV import | `pd.read_csv()` with encoding handling |
| **xhtml2pdf/pisa** | PDF generation | `render_to_pdf()` for financial documents |
| **reportlab** | PDF tooling | Dependency of xhtml2pdf |
| **python-decouple** | Environment config | `config('SECRET_KEY')`, `config('DEBUG')` |
| **psycopg2-binary** | PostgreSQL driver | Required for production DB in Docker |
| **gunicorn** | WSGI server | Docker CMD runs `gunicorn config.wsgi:application` |

### Environment Configuration

Uses `.env` file (not in git) for secrets:
```
SECRET_KEY=...
DEBUG=False
DB_ENGINE=django.db.backends.postgresql
DB_HOST=db
DB_USER=postgres
DB_PASSWORD=...
DB_NAME=cobranca_db
```

SQLite fallback for local dev if no env vars set.

### Database Models

- **SQLite** (default/dev): `db.sqlite3`
- **PostgreSQL** (production): Configured via `config/settings.py` database router
- Migrations stored in `core/migrations/`
- Supports upsert operations via `update_or_create()` for idempotent imports

## Code Quality & Testing Patterns

- **No unit tests present** in repo; focus on integration testing via manual CSV workflows
- **Admin interface** enabled (`django.contrib.admin`) for direct DB inspection
- **Migrations required** after model changes: `python manage.py makemigrations && migrate`

## Common Tasks for AI Agents

1. **Add new collection rule**: Extend `processar_regua.py` command with new `dias_atraso` condition
2. **Modify financial calculation**: Edit `Titulo.valor_atualizado` property; ensure fallback to defaults
3. **Import new CSV format**: Add column mapping in `importar_arquivo_view()` and `importar_csv` command (maintain flexibility pattern)
4. **Create new dashboard chart**: Use `annotate()` + `values()` pattern; add to `dashboard()` context
5. **Add new bill status**: Update `STATUS_CHOICES` in `Titulo` model; add new routes if needed

## Key Files Reference

- **Config**: `config/settings.py` (env-driven, WhiteNoise static files, Brazilian timezone)
- **Models**: `core/models.py` (Devedor, Titulo, HistoricoContato, ConfiguracaoFinanceira)
- **Views**: `core/views.py` (dashboard, detalhe_titulo, importar_arquivo_view)
- **URLs**: `core/urls.py` (main routes; no admin url registered here)
- **Commands**: `core/management/commands/` (importar_csv.py, processar_regua.py)
- **Templates**: `core/templates/core/` (dashboard.html, detalhe_titulo.html, boleto_impressao.html)
- **Utils**: `core/utils.py` (render_to_pdf)

## Deployment Notes

- **Docker**: Requires `Dockerfile` + `docker-compose.yml`; builds Python 3.12 slim with system dependencies for PDF libs (libcairo2, libpango, etc.)
- **Static files**: WhiteNoise middleware handles CSS/JS; uses `STATIC_URL = 'static/'` without collectstatic in Docker
- **Restart policy**: Docker compose set to `restart: always`; IPv6 disabled in container sysctls
