schema-name := "schema"

generate-model:
    @echo "Generating model"
    uv run datamodel-codegen --input {{schema-name}}.json --output src/github_feed/models/{{schema-name}}.py
    
run:
    uv run python src/github_feed/app.py