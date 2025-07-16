# Dockerfile

# 1. Use a slim Python base image
FROM python:3.11-slim

# 2. Install uv
#    - Install build tools, download installer, then clean up
RUN apt-get update && \
    apt-get install -y curl build-essential && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    apt-get remove -y curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# 3. Set working directory inside the container
#    All subsequent commands (COPY, RUN, CMD) operate relative to /usr/src/app
WORKDIR /usr/src/app

# 4. Copy only pyproject.toml and uv.lock for dependency resolution
#    This leverages Docker layer caching: dependencies only re-install when these files change
COPY pyproject.toml uv.lock* ./
COPY README.md ./
# 5. Install dependencies
RUN uv sync

# 6. Copy application code
#    - "app/" (local folder) → "./app" in container (=> /usr/src/app/app)
#      This preserves your folder structure inside the container.
#    - ".env" (local file) → "./.env" in container (=> /usr/src/app/.env)
#
#    After this step, inside the container you'll have:
#      /usr/src/app/pyproject.toml
#      /usr/src/app/poetry.lock
#      /usr/src/app/.env
#      /usr/src/app/app/   <- your application package root
COPY . .

EXPOSE 8150

# 7. Default command for web/API server
#    Runs Uvicorn against the module at "app.main:app"
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8150", "--reload"]