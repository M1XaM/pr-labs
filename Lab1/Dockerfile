FROM python:3.9-slim

WORKDIR /app

COPY server.py .
COPY client.py .

RUN chmod +x server.py client.py

EXPOSE 8080

CMD ["python3", "./server.py", "/app/content"]