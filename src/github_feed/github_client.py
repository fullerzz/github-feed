import logging
from asyncio import gather, to_thread
from datetime import UTC, datetime
from typing import Any

import aiohttp
import urllib3
from cachetools import TTLCache, cached
from cashews import cache
from multidict import CIMultiDictProxy
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
        logger.info("%s - %s", url, resp.status)
        unprocessed_responses: list[Any] = []
        if resp.status != 200:
            logger.error("Failed to retrieve starred repositories. Non-200 status returned: %s", resp.status)
            raise Exception("Failed to retrieve starred repositories")
        unprocessed_responses.append(resp.json())

        # Extract link header to get URL for next page
        link_header = parse_link_header(resp.headers)
        while link_header.next is not None:
            # Retrieve next page of results
            next_resp = self.http.request("GET", link_header.next)
            logger.info("PAGINATION! %s - %s", link_header.next, next_resp.status)
            unprocessed_responses.append(next_resp.json())
            # Update link_header before next iteration of while-loop
            link_header = parse_link_header(next_resp.headers)

        # Process all unprocessed responses after fetching all pages
        for response in unprocessed_responses:
            starred_repos.extend([Repository.model_validate(repo) for repo in response])

        return starred_repos

    @cache(ttl="2m", key="{url}")
    async def _get_starred_repositories(
        self, url: str, session: aiohttp.ClientSession, max_pages: int
    ) -> list[dict[str, Any]]:
        await to_thread(logger.info, "Fetching starred repos from %s", url)
        async with session.get(url) as resp:
            self._log_rate_limit(resp.headers, sampled=True)
            if resp.status == 404:
                raise Exception(f"No releases found: {url}")
            elif resp.status != 200:
                raise Exception(f"Failed to retrieve starred repos. Non-200 status returned for: {url}")

            if url.endswith(f"?page={max_pages}"):
                link_header = parse_link_header(resp.headers)  # type: ignore[arg-type]
                if link_header.next is not None:
                    logger.warning(
                        "Expected to reach the last page (%d), but found a next link: %s",
                        max_pages,
                        link_header.next,
                    )
                else:
                    logger.info("Reached the last page (%d) of starred repositories", max_pages)

            return await resp.json()  # type: ignore[no-any-return]

    async def get_starred_repositories_async(self) -> list[Repository]:
        url = f"{BASE_URL}/user/starred"
        max_pages = 16
        urls = [f"{url}?page={page}" for page in range(2, max_pages + 1)]
        urls.insert(0, url)
        async with aiohttp.ClientSession(
            headers=BASE_HEADERS | {"Authorization": f"Bearer {self.token}"}
        ) as session:
            responses = await gather(
                *[self._get_starred_repositories(url, session, max_pages) for url in urls],
                return_exceptions=True,
            )
            starred_repos = []
            for resp in responses:
                if isinstance(resp, BaseException):
                    logger.error("Error fetching starred repositories: %s", resp)
                    continue
                starred_repos.extend([Repository.model_validate(repo) for repo in resp])
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

    @cache(ttl="20m", key="{url}")
    async def _fetch_releases_for_repo(
        self, url: str, session: aiohttp.ClientSession
    ) -> list[Release] | BaseException:
        try:
            api_url = url.split("{")[0] if "{" in url else url
            await to_thread(logger.info, "Fetching latest release from %s", api_url)
            async with session.get(api_url) as response:
                self._log_rate_limit(response.headers, sampled=True)
                response.raise_for_status()
                data = await response.json()
                return [Release.model_validate(item) for item in data]
        except Exception as e:
            return e

    async def get_latest_releases_async(self, urls: list[str]) -> list[list[Release] | BaseException]:
        async with aiohttp.ClientSession(
            headers=BASE_HEADERS | {"Authorization": f"Bearer {self.token}"}
        ) as session:
            tasks = [self._fetch_releases_for_repo(url, session) for url in urls]
            results = await gather(*tasks, return_exceptions=True)
            return results

    def _log_rate_limit(self, resp_headers: "CIMultiDictProxy[str]", sampled: bool) -> None:
        if "x-ratelimit-limit" in resp_headers:
            limit = resp_headers["x-ratelimit-limit"]
            remaining = resp_headers.get("x-ratelimit-remaining", "unknown")
            used = resp_headers.get("x-ratelimit-used", "unknown")
            reset = resp_headers.get("x-ratelimit-reset", "unknown")
            if reset != "unknown":
                reset = datetime.fromtimestamp(int(reset), UTC).strftime("%Y-%m-%d %H:%M:%S%Z")

            if not sampled or (sampled and used != "unknown" and int(used) % 10 == 0):
                logger.info(
                    "Rate limit: %s, Remaining: %s, Used: %s, Reset: %s",
                    limit,
                    remaining,
                    used,
                    reset,
                )
