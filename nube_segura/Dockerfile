# ========================================================
# Dockerfile: Google Cloud Run - Entorno Seguro CENAM
# ========================================================
FROM python:3.11-slim

# Evitar escritura de .pyc y habilitar logs en tiempo real sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Instalar dependencias del sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario de seguridad sin privilegios de root (Hardening)
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Crear carpetas de almacenamiento efímero y asignar permisos al usuario seguro
RUN mkdir -p /app/generated_docs && chown -R appuser:appuser /app

# Cambiar al usuario no-root
USER appuser

# Exponer el puerto de Cloud Run
EXPOSE 8080

# Comando de inicio del servidor ASGI Uvicorn para Cloud Run
CMD ["sh", "-c", "python -m uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080} --workers 2"]
