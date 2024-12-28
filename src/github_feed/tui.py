from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Header, Label


class GitHubFeed(App[str]):
    CSS_PATH = "css/tui.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Horizontal(
                Label("Do you love Textual?", id="question"),
                Label("Current number of starred repos", id="starredReposCount"),
                classes="row",
            ),
            Horizontal(
                Button("Yes", id="yes", variant="primary"), Button("No", id="no", variant="error"), classes="row"
            ),
        )


if __name__ == "__main__":
    app = GitHubFeed()
    app.run()
