# Use Python 3.14 slim
FROM python:3.14-slim

# ----------------------------
# Instalar compiladores y dependencias de numpy
# ----------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    libblas-dev \
    liblapack-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------
# Crear directorio de trabajo
# ----------------------------
WORKDIR /app

# ----------------------------
# Copiar requirements e instalar dependencias
# ----------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------
# Copiar el código fuente
# ----------------------------
COPY . .

# ----------------------------
# Dar permisos al script de inicio
# ----------------------------
RUN chmod +x /app/start.sh

# ----------------------------
# Exponer puerto
# ----------------------------
EXPOSE 8000

# ----------------------------
# Comando por defecto
# ----------------------------
CMD ["/app/start.sh"]
