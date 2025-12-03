# 1. Imagem base
FROM python:3.12-slim

# 2. Configurações
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Workdir
WORKDIR /app

# 4. Instala dependências do sistema (Adicionado pkg-config)
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libpq-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Instala dependências Python
COPY requirements.txt /app/
RUN pip install --upgrade pip
# Tenta instalar binários primeiro para evitar compilação
RUN pip install -r requirements.txt --prefer-binary

# 6. Copia código
COPY . /app/

# 7. Comando
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]