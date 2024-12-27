import pathlib
from os import environ
import duckdb
from rich.pretty import pprint
from rich.traceback import install

from github_feed.github_client import GitHubClient
from github_feed.models import Repository

install(show_locals=False)


def get_new_releases() -> None:
    duckdb.read_json("starred_repos.json").show()


def save_starred_repos(repos: list[Repository], filename: str) -> None:
    with pathlib.Path(filename).open("w") as file:
        file.write("[\n")
        for i, repo in enumerate(repos):
            file.write(f"{repo.model_dump_json(indent=2)}")
            if i < len(repos) - 1:
                file.write(",\n")
            else:
                file.write("\n")
        file.write("]\n")


def retrieve_activity() -> None:
    token = environ["GITHUB_TOKEN"]
    client = GitHubClient(token)
    resp = client.get_user()
    pprint(resp)
    starred = client.get_starred_repositories()
    save_starred_repos(starred, "starred_repos.json")
    get_new_releases()


if __name__ == "__main__":
    retrieve_activity()
