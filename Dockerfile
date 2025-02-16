FROM python:3.13-slim

WORKDIR /app

RUN pip install poetry==2.1.0
COPY pyproject.toml poetry.lock poetry.toml ./
RUN poetry install --no-interaction --no-root

COPY src/ README.md LICENSE ./
RUN poetry build --no-interaction \
    && poetry install --no-interaction

# Create volume mount point for fixtures
RUN mkdir -p /app/config
VOLUME ["/app/config"]

ENV CONFIG_PATH=/app/config/users.yaml
ENV HOST=0.0.0.0
ENV PORT=8089

EXPOSE ${PORT}

ENTRYPOINT [ "./entrypoint.sh" ]
