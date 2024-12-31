from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from functools import cache
from os import getenv

from pydantic import BaseModel, SecretStr, ValidationError
from sqlalchemy.exc import IntegrityError, NoResultFound

from github_feed import utils
from github_feed.github_client import GitHubClient
from github_feed.models import Release, Repository
from github_feed.sql.client import DbClient
from github_feed.sql.models import Repository as SqlRepository

DEFAULT_DB_FILENAME = "stargazing.db"


@cache
def get_db_client(filename: str) -> DbClient:
    return DbClient(f"sqlite:///{filename}")


class Config(BaseModel):
    db_filename: str = DEFAULT_DB_FILENAME
    github_token: SecretStr


class Engine:
    def __init__(self) -> None:
        self.config = self.load_config()
        self.db = get_db_client(filename=self.config.db_filename)
        self.gh_client = GitHubClient(self.config.github_token.get_secret_value())

    def load_config(self) -> Config:
        db_filename = getenv("DB_FILENAME")
        github_token = getenv("GITHUB_TOKEN")
        config_inputs = {"github_token": github_token}
        if db_filename is not None:
            config_inputs["db_filename"] = db_filename
        return Config(**config_inputs)  # type: ignore[arg-type]

    def retrieve_starred_repos(self, refresh: bool = False) -> Sequence[SqlRepository]:
        """
        Returns list of starred repositories from the db.
        """
        if refresh:
            self.refresh_starred_repos()
        starred_repos = self.db.get_starred_repos()
        return starred_repos

    def refresh_starred_repos(self) -> None:
        """
        Retrieve starred repos from GitHub and populate the database.
        """
        starred_repos = self.gh_client.get_starred_repositories()
        for repo in starred_repos:
            self._refresh_starred_repo_in_table(repo)

    def _refresh_starred_repo_in_table(self, repo: Repository) -> None:
        """
        Inserts starred repo into table if not already present. Otherwise, the existing starred repo
        is updated with fresh data from the GitHub API.
        """
        raw_repo = repo.model_dump()
        try:
            self.db.add_repository(SqlRepository(**raw_repo))
        except IntegrityError:
            # Repo already exists in the db, so try to retrieve the existing row
            try:
                existing_repo = self.db.get_repository(repo.id)
            except NoResultFound:
                # TODO: Log this error and decide how to handle it
                return None
            existing_repo = utils.update_existing_repo(existing_repo, repo)
            self.db.update_repository(existing_repo)
            return None

    def retrieve_releases(self, start_time: datetime | None = None) -> list[Release]:
        """
        Retrieve repositories that have been updated since the given start time.
        If no start time is provided, a default of 2 days is used.
        """
        if start_time is None:
            # Default to 2-day window
            start_time = datetime.now(UTC) - timedelta(days=2)

        updated_repos = self.db.get_updated_repos(start_time)

        releases = []
        for repo in updated_repos:
            # FIXME: This logic doesn't work if there are multiple releases within the time window as only the latest release will be returned
            try:
                latest_release = self.gh_client.get_latest_release(repo.releases_url)
                if latest_release.created_at > start_time:
                    releases.append(latest_release)
            except ValidationError:
                # TODO: Log validation failure for repo
                pass
        releases.sort(key=lambda x: x.created_at, reverse=True)
        return releases
