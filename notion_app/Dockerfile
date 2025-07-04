# Stage 1: Builder Stage - Install Python dependencies
# Uses a specific, slim Debian-based Python image for a smaller footprint
FROM python:3.10-slim-buster AS builder


# Set the working directory inside the container
WORKDIR /app

# Copy only requirements.txt first to leverage Docker's build cache.
# If requirements.txt doesn't change, this layer (and pip install) will be cached.
COPY requirements.txt .

# Install Python dependencies.
# --no-cache-dir reduces the image size by not storing pip's cache.
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production Stage - Create the final, lean image
# Start from the same slim base image for consistency and small size
FROM python:3.10-slim-buster

# Set the working directory for the application
WORKDIR /app

# Install curl for the healthcheck command.
# Also update apt cache and clean up afterwards to keep image small.
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*
# ==========================================================

# Copy installed Python packages from the builder stage to the final image.
# This includes FastAPI, Uvicorn, and their dependencies.
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
# Copy the uvicorn executable from the builder stage
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Copy your application code into the container
COPY . .

# Expose the port that the FastAPI application will listen on inside the container.
# This is informational; actual port mapping for external access is done in docker-compose.yml.
EXPOSE 5000

# Define the command to run your application using Uvicorn.
# 'app:app' refers to the 'app' FastAPI instance found in 'app.py'.
# '--host 0.0.0.0' ensures the app listens on all network interfaces within the container,
# making it accessible from other containers in the Docker network (like Nginx).
# '--port 5000' specifies the internal port Uvicorn will listen on.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]