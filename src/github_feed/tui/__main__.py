from __future__ import annotations

from argparse import ArgumentParser

from github_feed.tui.app import GitHubFeedApp, ReleaseMode


def main() -> None:
    parser = ArgumentParser(
        prog="github-feed-tui", description="Browse starred repo releases in a Textual TUI"
    )
    parser.add_argument(
        "--window-days",
        type=int,
        default=None,
        help="Days to include in recent release mode (default: 30)",
    )
    parser.add_argument(
        "--all-history",
        action="store_true",
        help="Start in all history mode instead of recent mode",
    )
    args = parser.parse_args()

    app = GitHubFeedApp(release_window_days=args.window_days)
    if args.all_history:
        app.release_mode = ReleaseMode.ALL_HISTORY
    app.run()


if __name__ == "__main__":
    main()
