# syntax=docker/dockerfile:1

FROM python:3.13-slim-bookworm@sha256:2f2e5a876c71a6757f55ec57f2add0225ddaf01c802a33fcc29073943f94d907

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/workspace/.state/matplotlib \
    JUPYTER_CONFIG_DIR=/workspace/.state/jupyter \
    JUPYTER_DATA_DIR=/workspace/.state/jupyter-data \
    JUPYTER_RUNTIME_DIR=/workspace/.state/jupyter-runtime \
    KAGGLEHUB_CACHE=/workspace/.state/kagglehub \
    KERAS_BACKEND=jax

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        graphviz \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir \
        "keras==3.15.1" \
        "keras-hub==0.31.1" \
        "keras-tuner==1.4.8" \
        "jax[cuda12]==0.11.1" \
        "tensorflow==2.20.0" \
        "tensorflow-text==2.20.1" \
        "torch==2.14.0" \
        "numpy==2.5.2" \
        "pandas==3.0.5" \
        "scipy==1.18.1" \
        "scikit-learn==1.9.0" \
        "matplotlib==3.11.1" \
        "pillow==12.3.0" \
        "regex==2026.9.3" \
        "kagglehub==1.0.2" \
        "jupyterlab==4.6.3" \
        "ipykernel==7.3.0" \
        "pydot==4.0.1" \
    && python -m pip check

ENV XLA_PYTHON_CLIENT_PREALLOCATE=false \
    TF_FORCE_GPU_ALLOW_GROWTH=true

RUN python -m pip install --no-cache-dir "pytest==9.1.1" && python -m pip check

WORKDIR /workspace
