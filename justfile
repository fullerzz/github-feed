schema-name := "schema"

_default:
    @just --list

generate-model:
    @echo "Generating model"
    uv run datamodel-codegen --input {{schema-name}}.json --output src/github_feed/temp_models/{{schema-name}}.py

# run fastapi dev server   
run-dev:
    uv run fastapi dev src/github_feed/main.py

# run fastapi prod server
run-prod:
    uv run fastapi run src/github_feed/main.py

# run fastapi prod server with uvicorn directly
uvicorn:
    uv run uvicorn github_feed.main:app --host 0.0.0.0 --port 80

# run the ruff linter
lint:
    @echo "Running Ruff linter"
    uv run ruff check --fix .

# run the ruff formatter
fmt:
    @echo "Running Ruff formatter"
    uv run ruff format

# run the ruffer linter and formatter
ruff:
    @echo "Running Ruff linter and formatter"
    just lint fmt

_start-dmypy:
    @echo "Starting dmypy"
    -uv run dmypy start

# run mypy type checker
mypy: _start-dmypy
    @echo "Running mypy with the mypy daemon dmypy"
    uv run dmypy check src/github_feed

# build the docker image
build:
    @echo "Building Docker image"
    docker build -t github-feed-api .

# run the docker image
run:
    @echo "Running Docker image"
    docker compose up

# rebuild the docker image
rebuild:
    @echo "Rebuilding Docker image"
    docker compose up --build -d