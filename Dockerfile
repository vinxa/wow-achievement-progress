# Use a lightweight Python base image
FROM python:3.13.7-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install gunicorn

COPY . .
EXPOSE 5001

CMD ["gunicorn", "-b", "0.0.0.0:5001", "app:create_app()"]
