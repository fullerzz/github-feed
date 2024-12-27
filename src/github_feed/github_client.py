import urllib3

from github_feed.models import User

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
