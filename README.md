# Better Reviewer

## Abstract

An [Anki](https://apps.ankiweb.net) add-on that improves the everyday review
experience. Targets Anki 26.09+ (Python 3.13, PyQt6).

## Installation

Download `better_reviewer.ankiaddon` and double-click it (or use
**Tools → Add-ons → Install from file…**), then restart Anki.

## Development

This project uses [`uv`](https://github.com/astral-sh/uv). To install:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install everything the project needs, including the `anki` and `aqt`
libraries pinned to the same version as the target Anki release:

```
uv sync
```

The tool [`black`](https://github.com/psf/black) is used for formatting:

```
uv run black .
```

Tests run headlessly against the `anki` library:

```
uv run pytest
```

### Layout

```
src/better_reviewer/   the add-on itself (what ships in the .ankiaddon)
  manifest.json        package/folder name, display name, min Anki version
  config.json          default user config (editable in Anki's add-on dialog)
src/devtools/          dev scripts (not shipped)
tests/                 pytest suite
.anki-dev/             isolated Anki base folder for development (gitignored)
```

### How Anki loads add-ons

Anki imports every package in `<base>/addons21/` at startup. During
development the add-on source is symlinked there, so edits only need an Anki
restart. Users install a zipped `.ankiaddon` whose root holds the package
contents; `manifest.json`'s `package` field names the folder it unpacks into.

## Scripts

| Command | Effect |
| --- | --- |
| `uv run anki-dev` | Symlink the add-on into `.anki-dev/` and launch Anki on that isolated base (never touches your real collection). Sets `ANKIDEV=1` and exposes web views to Chromium DevTools at <http://localhost:8080>. Extra args pass through to Anki. |
| `uv run link` / `uv run unlink` | Create or remove only the dev symlink. |
| `uv run package` | Build `dist/better_reviewer.ankiaddon`. |

Set `ANKI_BIN` if Anki is not at `/Applications/Anki.app`. Add-on logs land in
`.anki-dev/logs/addons/better_reviewer/`.
