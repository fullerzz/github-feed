from rich.panel import Panel
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Header, Label, Static


class EnvVarPanel(Static):
    def on_mount(self) -> None:
        panel = Panel("[bold cyan]Environment variable is present[/]", title="$GITHUB_TOKEN", expand=False)
        self.update(panel)


class GitHubFeed(App[str]):
    CSS_PATH = "css/tui.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Horizontal(
                EnvVarPanel(shrink=True, id="envVarPanel"),
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
