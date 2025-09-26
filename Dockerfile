# Use a lightweight Python base image
FROM python:3.13.7-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 5001

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

CMD ["python", "app.py"]
