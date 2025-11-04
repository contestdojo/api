FROM python:3.10

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "contestdojo_api.main:app", "--host", "::", "--port", "8000"]
