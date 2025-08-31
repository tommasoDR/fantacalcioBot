FROM python:3.11-slim

# Installa Chromium e ChromeDriver (più affidabile)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]