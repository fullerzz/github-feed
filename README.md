# GitHub Feed

`github-feed` tracks release activity from your starred repositories.

It now supports two interfaces:
- A FastAPI REST API for programmatic access.
- A Textual TUI for interactive browsing in the terminal.

## Requirements

- Python 3.12+
- `uv`
- `GITHUB_TOKEN` environment variable

Optional environment variables:
- `DB_FILENAME` (default: `data/stargazing.db`)
- `RELEASE_WINDOW_DAYS` (default: `30`, used by TUI recent mode)

## Setup

```bash
uv sync
```

## Run the API

```bash
just run-dev
```

Useful endpoints:
- `GET /starred?refresh=true|false`
- `GET /releases?refresh=true|false`

## Run the TUI

```bash
just run-tui
```

Or run directly:

```bash
uv run github-feed-tui
```

TUI options:
- `--window-days <N>`: set recent-mode window (default: 30)
- `--all-history`: start in all-history mode

Release modes in the TUI:
- `Recent`: show releases in a configurable lookback window (default 30 days)
- `All History`: show all stored release history

Keyboard shortcuts:
- `h`: Home
- `s`: Starred repositories
- `r`: Releases
- `m`: Toggle release mode
- `right`: On Releases, open full-page notes for selected release
- `left`: On full-page notes, return to Releases
- `q`: Quit

## Development Checks

```bash
just ruff
just mypy
uv run pytest
```
