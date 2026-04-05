FROM python:3.13-slim

# Install uv directly into the container using the official binary image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first to maximize Docker layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies using uv into the container's virtual environment
RUN uv sync --frozen --no-dev

# Copy the rest of the application files
COPY . .

# Explicitly state the port we will listen on
EXPOSE 8000

# Start Uvicorn via the run.py script (which spins up 4 workers per container!)
CMD ["uv", "run", "python", "run.py"]
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY seed_data ./seed_data
COPY docker-entrypoint.sh ./
COPY run.py ./

RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

CMD ["/app/docker-entrypoint.sh"]
