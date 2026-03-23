# Use uv-enabled base image with Python 3.11
FROM ghcr.io/astral-sh/uv:python3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for building some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Optimize for caching: Copy pyproject.toml and uv.lock first
COPY pyproject.toml uv.lock ./

# Install dependencies into the container
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the application
COPY . .

# Ensure uv sync is fully done with project installed
RUN uv sync --frozen --no-dev

# Create dummy stop signal and log files if they don't exist
RUN touch STOP_SIGNAL strategy.log

# Expose port for Streamlit
EXPOSE 8501

# Add uv environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Default command (runs the dashboard via the uv-managed venv)
CMD ["streamlit", "run", "dashboard/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
