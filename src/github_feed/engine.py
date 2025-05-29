import logging
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from functools import cache
from os import environ, getenv

from pydantic import BaseModel, SecretStr, ValidationError
from sqlalchemy.exc import IntegrityError, NoResultFound

from github_feed.github_client import GitHubClient
from github_feed.lib import utils
from github_feed.lib.models import Release, Repository
from github_feed.sql.client import DbClient
from github_feed.sql.models import Release as SqlRelease
from github_feed.sql.models import Repository as SqlRepository

DEFAULT_DB_FILENAME = "data/stargazing.db"
logger = logging.getLogger(__name__)


@cache
def get_db_client(filename: str = DEFAULT_DB_FILENAME) -> DbClient:
    return DbClient(f"sqlite:///{filename}")


@cache
def get_github_client(token: str) -> GitHubClient:
    return GitHubClient(token)


class Config(BaseModel):
    db_filename: str = DEFAULT_DB_FILENAME
    github_token: SecretStr


class Engine:
    def __init__(self) -> None:
        self.config: Config = self.load_config()
        self.db: DbClient = get_db_client(filename=self.config.db_filename)
        self.gh_client: GitHubClient = get_github_client(self.config.github_token.get_secret_value())
        logger.info("Created new engine instance")

    def load_config(self) -> Config:
        db_filename = getenv("DB_FILENAME")
        github_token = environ["GITHUB_TOKEN"]
        config_inputs = {"github_token": github_token}

        if db_filename is not None:
            config_inputs["db_filename"] = db_filename

        return Config(**config_inputs)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]

    async def retrieve_starred_repos(self, refresh: bool = False) -> Sequence[SqlRepository]:
        """
        Returns list of starred repositories from the db.
        """
        if refresh:
            logger.info("Refreshing starred repositories")
            await self.refresh_starred_repos()
        starred_repos = self.db.get_starred_repos()
        logger.info("Retrieved %d starred repositories from the db", len(starred_repos))
        return starred_repos

    async def refresh_starred_repos(self) -> None:
        """
        Retrieve starred repos from GitHub and populate the database.
        """
        starred_repos = await self.gh_client.get_starred_repositories_async()
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
            logger.info("Added new starred repository to the db: %s", repo.full_name)
        except IntegrityError:
            # Repo already exists in the db, so try to retrieve the existing row
            try:
                existing_repo = self.db.get_repository(repo.id)
            except NoResultFound:
                # TODO: Log this error and decide how to handle it
                logger.error("IntegrityError was raised by no existing repo found for id %s", repo.id)
                return None
            existing_repo = utils.update_existing_repo(existing_repo, repo)
            self.db.update_repository(repository=existing_repo)
            logger.info("Updated existing starred repository in the db: %s", repo.full_name)
            return None

    def retrieve_releases(self, start_time: datetime | None) -> list[SqlRelease]:
        """
        Retrieve repositories that have been updated since the given start time.
        If no start time is provided, a default of 3 days is used.
        """
        if start_time is None:
            # Default to 3-day window
            start_time = datetime.now(UTC) - timedelta(days=3)
        logger.info("Retrieving releases since %s", start_time.isoformat())

        releases = self.db.get_releases(start_time)
        releases = list(releases)
        releases.sort(key=lambda x: x.created_at, reverse=True)
        logger.info("Retrieved %d releases from the db", len(releases))
        return releases

    def retrieve_fresh_releases(self, start_time: datetime | None = None) -> list[Release]:
        """
        Retrieve repositories that have been updated since the given start time.
        If no start time is provided, a default of 3 days is used.
        """
        if start_time is None:
            # Default to 3-day window
            start_time = datetime.now(UTC) - timedelta(days=3)
        logger.info("Retrieving repos updated since %s", start_time.isoformat())
        updated_repos = self.db.get_updated_repos(start_time)

        releases = []

        for repo in updated_repos:
            logger.info("Retrieving releases for repo %s", repo.full_name)
            # FIXME: This logic doesn't work if there are multiple releases within the time window as only the latest release will be returned
            try:
                latest_release = self.gh_client.get_latest_release(repo.releases_url)
                if latest_release.created_at > start_time:
                    releases.append(latest_release)
                    self.db.add_release(SqlRelease(**latest_release.model_dump()))
            except ValidationError as e:
                # TODO: Log validation failure for repo
                logger.warning(
                    "Validation error for repo %s: %s",
                    repo.full_name,
                    e.errors(include_input=False, include_url=False),
                )
            except IntegrityError:
                # We already have this release in the table
                logger.info("Release %s already exists in the db", repo.full_name)
            except Exception:
                logger.warning("Failed to retrieve release for repo %s", repo.full_name)

        releases.sort(key=lambda x: x.created_at, reverse=True)
        logger.info("Retrieved fresh %d releases", len(releases))
        return releases

    async def retrieve_fresh_releases_async(self, start_time: datetime | None = None) -> list[Release]:
        if start_time is None:
            # Default to 3-day window
            start_time = datetime.now(UTC) - timedelta(days=3)
        logger.info("Retrieving repos updated since %s", start_time.isoformat())
        updated_repos = self.db.get_updated_repos(start_time)

        # Fetch all releases for each updated repo asynchronously
        urls = [repo.releases_url for repo in updated_repos]
        all_results: list[list[Release] | BaseException] = await self.gh_client.get_latest_releases_async(
            urls
        )
        releases = []
        for repo, results in zip(updated_repos, all_results, strict=True):
            if isinstance(results, BaseException):
                logger.warning("Failed to retrieve releases for repo %s: %s", repo.full_name, results)
                continue
            for result in results:
                if isinstance(result, BaseException):
                    logger.warning("Failed to retrieve release for repo %s: %s", repo.full_name, result)
                    continue
                if result.created_at > start_time:
                    releases.append(result)
                    try:
                        self.db.add_release(SqlRelease(**result.model_dump()))
                    except IntegrityError:
                        logger.info("Release %s already exists in the db", result.name)
        releases.sort(key=lambda x: x.created_at, reverse=True)
        logger.info("Retrieved fresh %d releases", len(releases))
        return releases
