from pprint import pprint

import urllib3
from cachetools import TTLCache, cached
from urllib3.util import make_headers

from github_feed.models import Release, Repository, User
from github_feed.utils import parse_link_header

BASE_URL = "https://api.github.com"
BASE_HEADERS = make_headers(keep_alive=True, accept_encoding=True) | {
    "X-GitHub-Api-Version": "2022-11-28",
}


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
        pprint(resp.json())
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

    @cached(cache=TTLCache(maxsize=500, ttl=600))
    def get_latest_release(self, releases_url: str) -> Release:
        url = releases_url.replace("{/id}", "/latest")
        resp = self.http.request("GET", url)
        return Release.model_validate(resp.json())
