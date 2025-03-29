schema-name := "schema"

generate-model:
    @echo "Generating model"
    uv run datamodel-codegen --input {{schema-name}}.json --output src/github_feed/temp_models/{{schema-name}}.py
    
run:
    uv run fastapi dev --no-reload src/github_feed/main.py

tui:
    uv run textual run --dev src/github_feed/tui.py

lint:
    @echo "Running Ruff linter"
    uv run ruff check --fix .

fmt:
    @echo "Running Ruff formatter"
    uv run ruff format

ruff:
    @echo "Running Ruff linter and formatter"
    just lint fmt

start-dmypy:
    @echo "Starting dmypy"
    -uv run dmypy start

mypy: start-dmypy
    @echo "Running mypy with the mypy daemon dmypy"
    uv run dmypy check src/github_feed
