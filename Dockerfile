FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads/message_attachments

EXPOSE 8000

CMD ["sh", "-c", "echo Open the app at: http://localhost:8000 && exec uvicorn main:app --host 0.0.0.0 --port 8000"]
