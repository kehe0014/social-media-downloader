# ==============================================================================
# Optimized Dockerfile for Streamlit Application (Corrected & Enhanced)
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder (base image)
# ------------------------------------------------------------------------------
FROM python:3.10-slim AS builder

# Set build-time environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create a non-root user
RUN useradd --create-home --shell /bin/bash appuser

# ------------------------------------------------------------------------------
# Stage 2: Dependencies (for better caching)
# ------------------------------------------------------------------------------
FROM builder AS dependencies

WORKDIR /tmp

# Copy requirements file for caching optimization
COPY requirements.txt .

# Create a virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 3: Final runtime image
# ------------------------------------------------------------------------------
FROM python:3.10-slim

# Set runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true

# Install only necessary runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy virtual environment from dependencies stage
COPY --from=dependencies /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code with correct permissions
COPY --chown=appuser:appuser app/ .

# Ensure correct ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose Streamlit port
EXPOSE 8501

# ------------------------------------------------------------------------------
# Healthcheck (✅ Fixed)
# ------------------------------------------------------------------------------
# Streamlit does not expose /healthz by default. Use "/" as reliable health URL.
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/ || exit 1

# ------------------------------------------------------------------------------
# Run Streamlit application
# ------------------------------------------------------------------------------
CMD ["streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--server.enableCORS=false", \
    "--server.enableXsrfProtection=false"]
