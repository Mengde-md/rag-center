FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml ./
COPY requirements.lock ./
COPY app ./app
RUN pip install -r requirements.lock && pip install --no-deps . && useradd --create-home appuser
COPY alembic.ini ./
COPY migrations ./migrations
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec python -m app --host 0.0.0.0 --port 8000"]
