from typing import Any
import urllib3

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

    def get_user(self) -> dict[str, Any]:
        url = f"{BASE_URL}/user"
        resp = self.http.request("GET", url)
        return resp.json()
