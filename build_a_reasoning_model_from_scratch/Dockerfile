# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git libgomp1 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.lock /opt/requirements.lock
RUN python -m pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cu128 --require-hashes -r /opt/requirements.lock \
    && python -m pip check
WORKDIR /workspace
