FROM python:3.11-slim

WORKDIR /app

RUN pip install websockets

COPY server.py .

CMD ["python", "server.py"]