from datetime import UTC, datetime, timedelta
from os import environ

from pydantic import ValidationError
from rich.pretty import pprint
from rich.progress import track
from rich.traceback import install

from github_feed import out
from github_feed.github_client import GitHubClient
from github_feed.models import Release, Repository
from github_feed.sql.client import DbClient
from github_feed.sql.models import Repository as SqlRepository
from github_feed.sql.models import RunData

install(show_locals=False)


def retrieve_activity() -> list[Repository]:
    token = environ["GITHUB_TOKEN"]
    client = GitHubClient(token)
    resp = client.get_user()
    pprint(resp)
    starred = client.get_starred_repositories()
    return starred


def populate_table(repos: list[Repository], db: DbClient) -> None:
    for repo in repos:
        raw_repo = repo.model_dump()
        db.add_repository(SqlRepository(**raw_repo))


def check_updates(db: DbClient, last_checked: datetime | None) -> None:
    print(f"{last_checked=}")
    if last_checked is None:
        recently_updated = db.get_updated_repos(datetime.now(UTC) - timedelta(hours=8))
    else:
        recently_updated = db.get_updated_repos(last_checked)

    token = environ["GITHUB_TOKEN"]
    client = GitHubClient(token)
    releases: list[Release] = []
    # Iterate over recently updated repos and check for new releases
    for repo in track(recently_updated, description="Checking for new releases"):
        try:
            latest_release = client.get_latest_release(repo.releases_url)
            if latest_release.created_at > datetime.now(UTC) - timedelta(days=7):
                releases.append(latest_release)
        except ValidationError:
            print(f"Error validating release: {repo.name}")
    out.display_releases(releases)
    out.display_releases_panels(releases)


def main() -> None:
    db = DbClient(f"sqlite:///{environ['DB_FILENAME']}")
    last_run: RunData | None = db.get_last_run()
    # TODO: Enable the below commented lines based on env var or command line arg
    # starred_repos = retrieve_activity()
    # populate_table(starred_repos, db)
    # if last_run:
    #     check_updates(db, last_run.executed_at)
    # else:
    #     check_updates(db, None)
    check_updates(db, None)
    db.store_run(datetime.now(UTC))


if __name__ == "__main__":
    main()
