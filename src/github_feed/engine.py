import duckdb


def load_starred_repos() -> duckdb.DuckDBPyRelation:
    return duckdb.read_json("starred_repos.json")


def get_new_releases() -> None:
    duckdb.sql("SELECT * FROM read_json_auto('starred_repos.json') WHERE pushed_at > '2024-12-27T11:34:25Z'").show()
