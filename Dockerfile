# Dockerfile multi-etapa para API de Búsqueda Semántica MENU
# Optimizado para producción con imagen final slim

# ================================
# Etapa 1: Builder
# ================================
FROM python:3.11-slim as builder

# Metadatos
LABEL maintainer="MENU API Team"
LABEL description="API de Búsqueda Semántica MENU - Builder Stage"

# Variables de entorno para build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema necesarias para build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ================================
# Etapa 2: Runtime
# ================================
FROM python:3.11-slim as runtime

# Metadatos
LABEL maintainer="MENU API Team"
LABEL description="API de Búsqueda Semántica MENU - Production"
LABEL version="1.0.0"

# Variables de entorno para runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

# Instalar dependencias mínimas del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crear usuario no-root para seguridad
RUN groupadd -r menuapi && useradd -r -g menuapi menuapi

# Crear directorios necesarios
RUN mkdir -p /app /data/chroma_db && \
    chown -R menuapi:menuapi /app /data

# Copiar dependencias Python desde builder
COPY --from=builder /root/.local /root/.local

# Establecer directorio de trabajo
WORKDIR /app

# Copiar código de la aplicación
COPY --chown=menuapi:menuapi . .

# Crear archivo .env por defecto si no existe
RUN if [ ! -f .env ]; then cp .env.example .env; fi

# Cambiar a usuario no-root
USER menuapi

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando por defecto usando Gunicorn con workers Uvicorn
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "-b", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]