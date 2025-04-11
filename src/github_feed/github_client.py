import logging

import aiohttp
import urllib3
from cachetools import TTLCache, cached
from cashews import cache
from urllib3.util import make_headers

from github_feed.lib.models import Release, Repository, User
from github_feed.lib.utils import parse_link_header

BASE_URL = "https://api.github.com"
BASE_HEADERS = make_headers(keep_alive=True, accept_encoding=True) | {
    "X-GitHub-Api-Version": "2022-11-28",
}
logger = logging.getLogger(__name__)
cache.setup("mem://")


class GitHubClient:
    def __init__(self, token: str) -> None:
        self.token = token
        self.http = urllib3.PoolManager(
            maxsize=10,
            headers=BASE_HEADERS | {"Authorization": f"Bearer {self.token}"},
        )

    def get_user(self) -> User:
        url = f"{BASE_URL}/user"
        resp = self.http.request("GET", url)
        return User.model_validate_json(resp.data.decode())

    @cached(cache=TTLCache(maxsize=1, ttl=300))
    def get_starred_repositories(self) -> list[Repository]:
        starred_repos: list[Repository] = []
        url = f"{BASE_URL}/user/starred"
        resp = self.http.request("GET", url)
        if resp.status != 200:
            raise Exception("Failed to retrieve starred repositories")
        # Populate starred_repos list with initial results
        starred_repos.extend([Repository.model_validate(repo) for repo in resp.json()])

        # Extract link header to get URL for next page
        link_header = parse_link_header(resp.headers)
        while link_header.next is not None:
            # Retrieve next page of results
            next_resp = self.http.request("GET", link_header.next)
            # Populate starred_repos list with results
            starred_repos.extend([Repository.model_validate(repo) for repo in next_resp.json()])
            # Update link_header before next iteration of while-loop
            link_header = parse_link_header(next_resp.headers)

        return starred_repos

    @cached(cache=TTLCache(maxsize=500, ttl=1200))
    def get_latest_release(self, releases_url: str) -> Release:
        url = releases_url.replace("{/id}", "/latest")
        resp = self.http.request("GET", url)
        if resp.status == 404:
            raise Exception("No releases found for this repository.")
        elif resp.status != 200:
            raise Exception("Failed to retrieve latest release. Non-200 status returned.")
        return Release.model_validate(resp.json())

    @cache(ttl="20m", key="{releases_url}")
    async def _fetch_latest_release(self, releases_url: str, session: aiohttp.ClientSession) -> Release:
        from asyncio import to_thread

        url = releases_url.replace("{/id}", "/latest")
        await to_thread(logger.info, "Fetching latest release from %s", url)
        async with session.get(url) as resp:
            if resp.status == 404:
                raise Exception(f"No releases found: {url}")
            elif resp.status != 200:
                raise Exception(f"Failed to retrieve latest release. Non-200 status returned: {url}")
            return Release.model_validate(await resp.json())

    async def get_latest_releases_async(self, urls: list[str]) -> list[Release | BaseException]:
        from asyncio import gather

        async with aiohttp.ClientSession(
            headers=BASE_HEADERS | {"Authorization": f"Bearer {self.token}"}
        ) as session:
            return await gather(
                *[self._fetch_latest_release(url, session) for url in urls], return_exceptions=True
            )
