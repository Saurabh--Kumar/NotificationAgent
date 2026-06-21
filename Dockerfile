FROM python:3.12-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev curl postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --use-deprecated=legacy-resolver -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable and set ownership
RUN chmod +x /app/docker-entrypoint.sh \
    && chown -R appuser:appuser /app
USER appuser

# Use entrypoint script
ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]

# Expose port
EXPOSE 8000

# Default command (will be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
