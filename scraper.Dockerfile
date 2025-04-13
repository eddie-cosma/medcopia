FROM python:3.13

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/run_scraper.sh

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=America/New_York

CMD ["bash", "-c", "/app/run_scraper.sh >> /app/instance/scraper.log 2>&1"]
