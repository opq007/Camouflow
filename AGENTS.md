# Repository Guidelines

## Project Structure & Module Organization

```
app/
  core/              browser integration, fingerprints, proxies
  server.py           FastAPI server — REST API endpoints and WebSocket log streaming
  services/          scenario engine and executable step types
  static/            HTML/CSS/JS frontend (single-page application)
  storage/           local data persistence (SQLite helpers)
  ui/http_app.py     entry point bootstrap (launches uvicorn + opens browser)
  utils/             general helpers (logging, parsing)
docs-site/           Retype-based documentation (Markdown -> GH Pages)
scenaries/           example scenario JSON files shipped with the build
images/              screenshots referenced by README
```

> The old PyQt6/QML UI layer (`app/ui/bridge/`, `app/ui/tabs/`, `app/ui/qml_app.py`, `app/qml/`) still exists on disk but is no longer imported. The active UI is the HTML frontend in `app/static/` served by `app/server.py`.

`main.py` at the repo root is a thin wrapper that imports and calls `app.main:main`, which now delegates to `app.ui.http_app:run_http_app`.

## Build, Test, and Development Commands

| Command | Purpose |
|---|---|
| `pip install -r requirements.txt` | Install Python dependencies (Python 3.12 recommended). |
| `python main.py` | Launch the desktop application (starts server + opens browser). |
| `python -m uvicorn app.server:app --reload` | Development server with auto-reload on `http://127.0.0.1:8000`. |
| `build.bat` | Build a Windows executable via PyInstaller. Output in `dist\CamouFlow\`. |
| `python -m compileall app` | Static syntax check on the `app` package. |
| `npx retype build` (from `docs-site/`) | Build the documentation site. |

Use a virtual environment (`py -3.12 -m venv .venv`) before installing dependencies.

## Coding Style & Naming Conventions

- **Python** follows PEP 8. Four-space indentation, `snake_case` for modules/functions/variables, `PascalCase` for classes. Imports use `from __future__ import annotations` and standard-library-first ordering.
- **API routes** in `app/server.py` are grouped by domain (`/api/profiles`, `/api/scenarios`, etc.) and use the `api_` prefix for handler function names.
- **Frontend** CSS uses CSS custom properties (theming) in `app/static/css/style.css`. JS in `app/static/js/app.js` is vanilla ES — no build step or framework. HTML in `app/static/index.html` follows the sidebar + page-containers SPA pattern.
- Heavy runtime dependencies (BrowserInterface, scenario engine) are imported lazily inside the API handler functions to keep the server module lightweight on startup.

## Testing Guidelines

There is no automated test suite yet. Before submitting changes, run at minimum:

```bat
python -m compileall app
```

This catches syntax errors across the `app` package. Manual smoke testing of affected views (load the SPA in a browser, navigate pages, exercise API calls) is expected. For API-level testing, start the dev server and hit endpoints with `curl` or the browser dev tools.

## Commit & Pull Request Guidelines

- Commit messages use short, imperative summaries (e.g. "fix WebGL startup crash and locale consistency", "Update desktop UI and documentation"). No formal prefix convention (`feat:`, `fix:`) is enforced.
- Reference relevant issues or context in the body when needed.
- Pull requests should describe what changed and why. Include screenshots or screen recordings for UI-altering changes (both the SPA frontend and the old QML views).

## Documentation

User-facing documentation lives under `docs-site/docs/` as Markdown files built with [Retype](https://retype.com/). The site is deployed to GitHub Pages via `.github/workflows/docs.yml` on every push to `main`.

- Scenario step types are documented individually under `docs-site/docs/steps/`.
- UI pages are documented under `docs-site/docs/ui/`.
- Navigation trees are defined in `index.yml` files within each directory.