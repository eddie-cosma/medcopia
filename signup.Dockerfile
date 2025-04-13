FROM python:3.13

WORKDIR /app

RUN apt-get update && \
    apt-get install -y && \
    pip3 install uwsgi

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD [ "uwsgi", "--ini", "/app/uwsgi.ini"]
