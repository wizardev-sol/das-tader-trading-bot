FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/
COPY pyproject.toml .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 9306

CMD ["python", "-m", "src.main"]

