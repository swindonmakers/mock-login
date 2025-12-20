FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

# Create volume mount point for fixtures
RUN mkdir -p /app/config
VOLUME ["/app/config"]

ENV HOST=0.0.0.0
ENV PORT=8089

EXPOSE ${PORT}

ENTRYPOINT [ "./entrypoint.sh" ]
