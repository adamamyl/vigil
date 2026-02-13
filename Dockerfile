FROM ghcr.io/astral-sh/uv:python3.12-alpine
RUN apk add --no-cache ffmpeg
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project
COPY . .
ENV PYTHONPATH=/app
CMD ["uv", "run", "python", "app/main.py"]