# Use Python 3.11 slim as base image
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Install Poetry and add to PATH
RUN curl -sSL https://install.python-poetry.org | python3 - && \
  export PATH="/root/.local/bin:$PATH" && \
  echo 'export PATH="/root/.local/bin:$PATH"' >> /root/.bashrc

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
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Set ownership and permissions
RUN chown -R botuser:botuser /app
RUN chmod -R 755 /app
RUN chmod 644 /app/.env
RUN chmod -R 777 /app/logs

# Switch to non-root user
USER botuser

# Run the bot
CMD ["python", "bot.py"]
