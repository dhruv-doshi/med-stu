# One-service Railway/Render image: FastAPI serves the exported Next.js app and
# retains ownership of the Vaani WebSocket and webhook endpoints.
FROM node:22-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
ARG NEXT_PUBLIC_API_BASE_URL=
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN npm run build

FROM python:3.13-slim AS runtime
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev --no-install-project
COPY backend ./backend
COPY --from=frontend-build /app/frontend/out ./frontend/out
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app/backend
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
