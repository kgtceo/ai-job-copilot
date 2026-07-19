# Full control over build + run. Railway's auto-detection builder (Railpack)
# wasn't installing the Python deps, so we build explicitly. When a Dockerfile is
# present, Railway uses it and skips Railpack/Nixpacks entirely.

FROM python:3.12-slim

WORKDIR /app

# Copy only what's needed to build + install the package (the API runtime needs
# the src package; evals/tests/web are not needed in the image).
COPY pyproject.toml README.md ./
COPY src ./src

# Installs the package AND its dependencies (fastapi, uvicorn, anthropic, …).
RUN pip install --no-cache-dir .

# Railway injects $PORT at runtime; default to 8000 for local `docker run`.
CMD ["sh", "-c", "python -m uvicorn job_copilot.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
