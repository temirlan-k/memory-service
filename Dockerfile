FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    APPLICATION_PATH="/app" \
    UV_SYSTEM_PYTHON=1 \
    UV_PROJECT_ENVIRONMENT="/opt/venv" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
ENV PATH="$UV_PROJECT_ENVIRONMENT/bin:$PATH"

WORKDIR $APPLICATION_PATH

COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /uvx /bin/
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY uv.lock pyproject.toml /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

RUN chmod +x docker-entrypoint.sh

EXPOSE 8080

RUN useradd -m appuser
USER appuser

CMD ["/bin/bash", "./docker-entrypoint.sh"]