FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY start.py ./start.py
COPY setup_webhook.py ./setup_webhook.py
COPY check_setup.py ./check_setup.py

# start.py prepares a combined standard + Russian Trusted CA bundle first,
# then launches FastAPI on Bothost's PORT.
CMD ["python", "start.py"]
