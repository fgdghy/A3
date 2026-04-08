FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data/circuit-breaker && chmod 777 /data/circuit-breaker

EXPOSE 3000

CMD ["python", "app.py"]