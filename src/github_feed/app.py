from datetime import UTC, datetime, timedelta
from os import environ

from pydantic import ValidationError
from rich.pretty import pprint
from rich.traceback import install

from github_feed import out
from github_feed.github_client import GitHubClient
from github_feed.models import Release, Repository
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
    releases: list[Release] = []
    # Iterate over recently updated repos and check for new releases
    for repo in recently_updated:
        try:
            latest_release = client.get_latest_release(repo.releases_url)
            if latest_release.created_at > datetime.now(UTC) - timedelta(days=7):
                releases.append(latest_release)
        except ValidationError:
            print(f"Error validating release: {repo.name}")
    out.display_releases(releases)


def main() -> None:
    # starred_repos = retrieve_activity()
    db = DbClient(f"sqlite:///{environ['DB_FILENAME']}")
    # populate_table(starred_repos, db)
    check_updates(db)


if __name__ == "__main__":
    main()
