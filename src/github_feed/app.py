from os import environ

from rich.pretty import pprint
from rich.traceback import install

from github_feed import engine, utils
from github_feed.github_client import GitHubClient
from github_feed.models import Repository
from github_feed.sql.client import DbClient
from github_feed.sql.models import Repository as SqlRepository

install(show_locals=False)


def retrieve_activity() -> list[Repository]:
    token = environ["GITHUB_TOKEN"]
    client = GitHubClient(token)
    resp = client.get_user()
    pprint(resp)
    starred = client.get_starred_repositories()
    # utils.save_starred_repos(starred, "starred_repos.json")
    return starred


def test_db_client(repos: list[Repository]) -> None:
    db_url = f"sqlite:///{environ["DB_FILENAME"]}"
    db = DbClient(db_url)
    for repo in repos:
        raw_repo = repo.model_dump()
        db.add_repository(SqlRepository(**raw_repo))
    print("DB updated")


if __name__ == "__main__":
    starred_repos = retrieve_activity()
    # engine.get_new_releases()
    test_db_client(starred_repos)
