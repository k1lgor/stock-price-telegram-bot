# Use Python 3.11 Alpine as base image
FROM python:3.11-alpine as builder

# Install system dependencies
RUN apk add --no-cache \
  gcc \
  musl-dev \
  python3-dev \
  libffi-dev \
  openssl-dev

# Install Poetry via pip
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY bot.py config.py database.py stock_service.py ./

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --no-root

# Create necessary directories
RUN mkdir -p logs

# Copy environment variables
COPY .env ./

# Create a non-root user and group
RUN addgroup -S botuser && adduser -S botuser -G botuser

# Set ownership and permissions
RUN chown -R botuser:botuser /app
RUN chmod -R 755 /app
RUN chmod 644 /app/.env
RUN chmod -R 777 /app/logs

# Switch to non-root user
USER botuser

# Expose port
EXPOSE 8080

# Run the bot
CMD ["python", "bot.py"]
