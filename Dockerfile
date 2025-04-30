FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt
RUN pip install gunicorn

# Используем Gunicorn вместо встроенного сервера Flask
CMD ["gunicorn", "--bind", "0.0.0.0:80", "wsgi:app"]