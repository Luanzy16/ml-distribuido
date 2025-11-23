FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY .env .env
COPY start.sh .

RUN chmod +x /app/start.sh

EXPOSE 8000
CMD ["/app/start.sh"]
