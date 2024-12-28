schema-name := "schema"

generate-model:
    @echo "Generating model"
    uv run datamodel-codegen --input {{schema-name}}.json --output src/github_feed/temp_models/{{schema-name}}.py
    
run:
    uv run python src/github_feed/app.py

tui:
    uv run textual run src/github_feed/tui.py
