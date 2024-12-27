import urllib3

from github_feed.models import Release, Repository, User
from github_feed.utils import parse_link_header

BASE_URL = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str) -> None:
        self.token = token
        self.http = urllib3.PoolManager(
            maxsize=10,
            headers={
                "X-GitHub-Api-Version": "2022-11-28",
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )

    def get_user(self) -> User:
        url = f"{BASE_URL}/user"
        resp = self.http.request("GET", url)
        return User.model_validate_json(resp.data.decode())

    def get_starred_repositories(self) -> list[Repository]:
        starred_repos: list[Repository] = []
        url = f"{BASE_URL}/user/starred"
        resp = self.http.request("GET", url)
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

    def get_latest_release(self, releases_url: str) -> Release:
        url = releases_url.replace("{/id}", "/latest")
        resp = self.http.request("GET", url)
        return Release.model_validate(resp.json())
