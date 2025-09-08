FROM python:3.12-slim-bullseye AS builder

RUN pip install uv

WORKDIR /app

COPY pyproject.toml /app
COPY uv.lock /app

RUN uv export --format requirements-txt --output-file requirements.txt && \
    pip install --no-cache-dir --prefix /install -r requirements.txt

FROM python:3.12-slim-bullseye AS runtime

WORKDIR /app
COPY --from=builder /install /usr/local

COPY main.py /app

CMD ["sh", "-c", "python main.py"]
