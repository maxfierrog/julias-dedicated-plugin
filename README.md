# Julia's Dedicated Plugin

## Abstract

A personal, actively maintained [Anki](https://apps.ankiweb.net) study suite:
one add-on, one settings screen, one design, built for a single student and
kept working across Anki releases. See [`docs/product.md`](docs/product.md).
Targets Anki 26.09+ (Python 3.13, PyQt6).

## Installation

Download `julias_dedicated_plugin.ankiaddon` and double-click it (or use
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
src/julias_dedicated_plugin/   the add-on itself (what ships in the .ankiaddon)
  manifest.json        package/folder name, display name, min Anki version
  config.json          unused placeholder; settings live in the collection
                       (Tools > Add-ons > Config opens the Customize window)
src/devtools/          dev scripts (not shipped)
tests/                 pytest suite
.anki-dev/             isolated Anki base folder for development (gitignored)
```

### How Anki loads add-ons

Anki imports every package in `<base>/addons21/` at startup. During
development the add-on source is symlinked there, so edits only need an Anki
restart. Users install a zipped `.ankiaddon` whose root holds the package
contents; `manifest.json`'s `package` field names the folder it unpacks into.

### Releasing to AnkiWeb

Users get the add-on from [AnkiWeb](https://ankiweb.net/shared/addons), which
gives it a numeric code and lets Anki offer updates on startup.

1. Bump the version in `src/julias_dedicated_plugin/version.py` and `manifest.json`.
2. `uv run pytest && uv run package`
3. Upload `dist/julias_dedicated_plugin.ankiaddon` via the Upload button on the
   AnkiWeb add-ons page (web form only; there is no upload API).

Rules this imposes on the code:

- **Never hardcode the folder name.** AnkiWeb installs into
  `addons21/<numeric id>/`. Use relative imports and
  `mw.addonManager.addon_from_module(__name__)` (e.g. for `/_addons/<folder>/`
  web-export URLs). A test enforces this.
- **Persistent data goes in `user_files/`.** Updates replace the whole folder;
  only `user_files/` (and user config in `meta.json`) survive.
- **Archive is flat with no `__pycache__`.** AnkiWeb rejects anything else;
  `uv run package` already does this.

## Scripts

| Command | Effect |
| --- | --- |
| `uv run anki-dev` | Symlink the add-on into `.anki-dev/` and launch Anki on that isolated base (never touches your real collection). Sets `ANKIDEV=1` and exposes web views to Chromium DevTools at <http://localhost:8080>. Extra args pass through to Anki. |
| `uv run link` / `uv run unlink` | Create or remove only the dev symlink. |
| `uv run package` | Build `dist/julias_dedicated_plugin.ankiaddon`. |
| `uv run seed` | Rebuild the dev collection: original MCAT-style notes (an AnKing-like cloze note type plus stock Basic/Cloze; images, tables, MathJax) with ~4 months of simulated review history, a backlog due today, and leeches. Deterministic; `--days`, `--seed`. Quit the dev Anki first. |
| `uv run install-addon <code>...` | Install AnkiWeb add-ons (by their numeric code) into the dev profile, as Anki's Get Add-ons does. Restart the dev Anki afterwards. |
| `uv run screenshot [out.png]` / `uv run anki-js "<expr>"` | Screenshot, or evaluate JS in, a running dev Anki web view (default: the main one) over DevTools. |
| `uv run anki-goto home\|deck\|review\|answer [--shot out.png]` | Navigate the running dev Anki (optionally screenshotting the whole window). |
| `uv run simulate` | Add simulated history to whatever is in the dev collection, e.g. a real deck imported via File → Import. Only works on a collection with no reviews yet. |

Set `ANKI_BIN` if Anki is not at `/Applications/Anki.app`. Add-on logs land in
`.anki-dev/logs/addons/julias_dedicated_plugin/`.
