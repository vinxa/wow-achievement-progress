FROM python:3.14.0-alpine

RUN apk add --no-cache \
    build-base \
    linux-headers

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install gunicorn

COPY . .
EXPOSE 5001

CMD ["gunicorn", "-b", "0.0.0.0:5001", "app:create_app()"]
