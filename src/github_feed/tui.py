from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Header

from github_feed.components.env_var_panel import EnvVarPanel
from github_feed.components.metadata_panel import MetadataPanel


class GitHubFeed(App[str]):
    CSS_PATH = "css/tui.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Horizontal(
                EnvVarPanel(shrink=True, id="envVarPanel"),
                MetadataPanel(323, id="metadataPanel"),
                classes="row",
            ),
            Horizontal(
                Button("Check for New Releases", id="checkReleases", variant="primary"),
                Button("Refresh List of Starred Repos", id="checkStarred", variant="error"),
                classes="row",
            ),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "checkReleases":
            self.notify("Check releases button pressed!")
        elif button_id == "checkStarred":
            self.notify("Check starred button pressed!")


if __name__ == "__main__":
    app = GitHubFeed()
    app.run()
