# Use an official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the console
ENV PYTHONUNBUFFERED True

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy local code to the container image
COPY . ./

# Expose port (Render/Railway default is often configured via PORT env var)
# We default to 8000 if not set. Uvicorn picks it up below.
ENV PORT 8000
EXPOSE $PORT

# Run the web service on container startup using uvicorn.
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT
