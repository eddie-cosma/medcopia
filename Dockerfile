FROM python:3.13

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y && \
    pip3 install uwsgi

# Copy requirements file first for better cache usage
COPY requirements.txt .

# Install Python dependencies including uwsgi
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables (these should be overridden at runtime)
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port 8000 for uwsgi
EXPOSE 8000

# Start uwsgi
CMD [ "uwsgi", "--ini", "/app/uwsgi.ini"]
