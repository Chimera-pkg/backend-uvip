# ---- Build stage ----
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system deps needed for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime stage ----
FROM python:3.12-slim

# Install only runtime libs (no compiler)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r uvip && useradd -r -g uvip -d /app -s /sbin/nologin uvip

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY main.py .
COPY app/ app/
COPY static/ static/

# Create upload directories with correct ownership
RUN mkdir -p uploads/photos && chown -R uvip:uvip /app

# Switch to non-root user
USER uvip

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/ || exit 1

EXPOSE 8000

# Run with 4 workers (adjust based on VPS RAM)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
