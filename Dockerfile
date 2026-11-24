# CPU build by default. For NVIDIA GPUs build with:
#   docker build --build-arg LLAMA_CMAKE_ARGS="-DGGML_CUDA=on" -t ggufbox:cuda .
# (and run with --gpus all, using a CUDA base image if you need the full toolkit)
FROM python:3.12-slim AS build
ARG LLAMA_CMAKE_ARGS=""
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake git \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /w
COPY requirements.txt requirements-engine.txt ./
RUN python -m venv /venv && /venv/bin/pip install --no-cache-dir -r requirements.txt \
    && CMAKE_ARGS="${LLAMA_CMAKE_ARGS}" /venv/bin/pip install --no-cache-dir -r requirements-engine.txt

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/* && useradd -m -u 1000 app
COPY --from=build /venv /venv
WORKDIR /srv
COPY app ./app
ENV PATH="/venv/bin:$PATH" GGUFBOX_MODELS_DIR=/models GGUFBOX_DATA_DIR=/data PYTHONUNBUFFERED=1
RUN mkdir -p /models /data && chown app /models /data
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -fs http://localhost:8000/api/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
