FROM python:3.10-slim

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (none really needed for instagrapi/instaloader on slim, but keeping fit)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for session files (mounted volume will map here)
# and webdata directories
RUN mkdir -p SessionFiles webdata/csv\ uploads webdata/csv\ downloads 

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
