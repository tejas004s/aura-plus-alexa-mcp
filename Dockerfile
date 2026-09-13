FROM python:3.10-slim

LABEL maintainer="Aura+ Team"
LABEL description="Aura+ Autonomous Alexa+ Concierge MCP Server"
LABEL org.opencontainers.image.source="https://github.com/tejas004s/aura-plus-alexa-mcp"

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose MCP server port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run with uvicorn
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
