# Usa Python slim para que sea liviano
FROM python:3.14-slim

# Set workdir
WORKDIR /app

# Copia requirements y los instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia la app completa
COPY app/ ./app/
COPY start.sh .

# Da permisos de ejecución al script
RUN chmod +x start.sh

# Expone puerto por defecto (el que pongas en .env)
EXPOSE 8000

# Comando por defecto
CMD ["/app/start.sh"]
