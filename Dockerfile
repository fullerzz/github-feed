# syntax=docker/dockerfile:1
# check=error=true

# Install uv
FROM python:3.13-slim AS builder

# Install curl for health checks
RUN apt-get update && apt-get install -y curl
RUN apt-get clean && \
  rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

ADD . /app

# Change the working directory to the `app` directory
WORKDIR /app

ENV UV_LINK_MODE=copy

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen

# Run the application
CMD ["uv", "run", "fastapi", "run", "src/github_feed/main.py", "--port", "80"]
