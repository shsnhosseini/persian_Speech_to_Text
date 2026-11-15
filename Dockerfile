# ---------------------------------------------------------------
# Persian Speech-to-Text (Streamlit) — Dockerfile
# Build:  docker build -t speech-to-text .
# Run:    docker run -p 8501:8501 --env-file .env speech-to-text
# ---------------------------------------------------------------

FROM python:3.12-slim AS builder

# Install build dependencies (if any compiled wheels are needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------
# Runtime stage — smaller final image
# ---------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

# Copy the virtualenv from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Streamlit configuration: bind to all interfaces so Docker port mapping works
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Copy application code
COPY app.py .

# Create a non-root user and switch to it
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose the Streamlit port
EXPOSE 8501

# Healthcheck: Streamlit serves a ready page on /_stcore/health
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://0.0.0.0:8501/_stcore/health', timeout=5)" || exit 1

ENTRYPOINT ["streamlit", "run", "app.py"]
