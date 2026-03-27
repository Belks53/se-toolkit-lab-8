# syntax=docker/dockerfile:1

# Stage 1: Build dependencies
FROM ghcr.io/astral-sh/uv:python3.14-bookworm AS builder

WORKDIR /app

# Copy workspace root files for dependency resolution
COPY --from=workspace pyproject.toml uv.lock ./
COPY --from=workspace nanobot/pyproject.toml ./nanobot/pyproject.toml
COPY --from=workspace nanobot-websocket-channel/pyproject.toml ./nanobot-websocket-channel/pyproject.toml
COPY --from=workspace nanobot-websocket-channel/nanobot_webchat ./nanobot-websocket-channel/nanobot_webchat
COPY --from=workspace mcp/pyproject.toml ./mcp/pyproject.toml
COPY --from=workspace mcp/mcp_lms ./mcp/mcp_lms

# Install nanobot with its workspace dependencies (non-editable)
# This also installs mcp and nanobot-webchat as workspace members
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package nanobot --package lms-mcp --no-editable

# Copy the rest of nanobot source from workspace
COPY --from=workspace nanobot/entrypoint.py ./nanobot/entrypoint.py
COPY --from=workspace nanobot/config.json ./nanobot/config.json
COPY --from=workspace nanobot/workspace/ ./nanobot/workspace/
COPY --from=workspace mcp/ ./mcp/

# Stage 2: Runtime
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app/nanobot

# Copy virtualenv from builder
COPY --from=builder /app/.venv /app/nanobot/.venv

# Copy project files
COPY entrypoint.py ./
COPY config.json ./
COPY workspace/ ./workspace/

# Copy MCP server
COPY --from=builder /app/mcp /app/mcp

# Set PATH and PYTHONPATH to include uv environment and MCP
ENV PATH="/app/nanobot/.venv/bin:$PATH"
ENV PYTHONPATH="/app/nanobot/.venv/lib/python3.14/site-packages:/app/mcp"

# Default command
CMD ["python", "/app/nanobot/entrypoint.py"]
