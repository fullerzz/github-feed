import duckdb


def get_new_releases() -> None:
    duckdb.read_json("starred_repos.json").show()
