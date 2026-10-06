FROM python:3.11-slim

WORKDIR /app

COPY evaluation/requirements.txt /app/evaluation/requirements.txt
RUN pip install --no-cache-dir -r /app/evaluation/requirements.txt

COPY backend /app/backend
COPY evaluation /app/evaluation

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "evaluation.run"]
