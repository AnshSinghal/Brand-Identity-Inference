# Use official Python image
FROM python:3.11-slim

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright (User provided list)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libnspr4 \
    libatk1.0-0t64 \
    libatk-bridge2.0-0t64 \
    libcups2t64 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2t64 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libgtk-3-0t64 \
    libatspi2.0-0t64 \
    libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements/lock files first for caching
COPY requirements.txt .
# If you have pyproject.toml/uv.lock in backend, copy them too:
# COPY pyproject.toml uv.lock ./

# Install Python dependencies using uv (much faster)
# --system installs into system python, compatible with docker
RUN uv pip install --system --no-cache -r requirements.txt && \
    playwright install chromium && \
    rm -rf /root/.cache/ms-playwright/download/firefox* && \
    rm -rf /root/.cache/ms-playwright/download/webkit*

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
