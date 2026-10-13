FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY pyproject.toml ./
COPY src ./src
RUN pip install .

USER app
EXPOSE 8000

CMD ["sh", "-c", "uvicorn ci_failure_spike.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]

