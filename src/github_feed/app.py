from datetime import UTC, datetime, timedelta
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


def populate_table(repos: list[Repository], db: DbClient) -> None:
    for repo in repos:
        raw_repo = repo.model_dump()
        db.add_repository(SqlRepository(**raw_repo))


def check_updates(db: DbClient) -> None:
    # TODO: Do we want to check if any updates in last day or check if any updates since last time the script ran?
    # For now, we'll just check for updates in the last day
    recently_updated = db.get_updated_repos(datetime.now(UTC) - timedelta(days=1))
    token = environ["GITHUB_TOKEN"]
    client = GitHubClient(token)
    for repo in recently_updated:
        pprint(repo.model_dump())
        releases = client.get_releases(repo.releases_url)
        for release in releases:
            output = {
                "tag": release["tag_name"],
                "name": release["name"],
                "published_at": release["published_at"],
                "created_at": release["created_at"],
                "url": release["html_url"],
                "body": release["body"],
            }
            pprint(output)
        exit(0)


def main() -> None:
    # starred_repos = retrieve_activity()
    db = DbClient(f"sqlite:///{environ['DB_FILENAME']}")
    # populate_table(starred_repos, db)
    check_updates(db)


if __name__ == "__main__":
    main()
