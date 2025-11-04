FROM python:3.10

WORKDIR /app
RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false
RUN poetry install --only main

COPY . .

EXPOSE 8000
CMD ["uvicorn", "contestdojo_api.main:app", "--host", "::", "--port", "8000"]
