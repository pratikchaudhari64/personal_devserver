# Dockerfile for personal_website/minimalistic_python/Dockerfile

# Use Python slim image for Flask application
FROM python:3.10-slim-bullseye

# Set working directory
WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose port 3000 (Flask app runs on this port internally)
EXPOSE 3001

# Set Python to run in unbuffered mode for better logging
# ENV PYTHONUNBUFFERED=1

# Run the Flask application
# CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "3001"] 
CMD ["gunicorn", "fastapi_app:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:3001"]