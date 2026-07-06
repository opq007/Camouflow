# CamouFlow

CamouFlow is a local desktop workspace for browser profiles, proxies and visual automation scenarios.

The app is built with **Python + FastAPI/HTML** and runs automation through **Camoufox / CloakBrowser** with local storage for profiles, settings, scenarios, proxy pools and logs. The UI is served as a web app in your default browser, making it cross-platform (Windows, Linux, macOS).

## Screenshots

> **Note:** Screenshots below show the pre-refactor PyQt6 UI. The HTML UI follows the same premium dark theme and page layout.

| Dashboard | Profiles |
|---|---|
| ![Dashboard](images/dashboard.png) | ![Profiles](images/profiles.png) |

| Browser settings | Proxies |
|---|---|
| ![Browser settings](images/browser.png) | ![Proxies](images/proxies.png) |

| Scenarios | Logs |
|---|---|
| ![Scenarios](images/scenarios.png) | ![Logs](images/logs.png) |

## Current features

### Dashboard

- profile, browser, scenario and proxy counters
- running session list
- recent activity feed
- quick navigation actions

### Profiles

- create, edit and delete browser profiles
- bulk import profiles with an account parse template
- start and stop profile browser sessions
- assign proxy data to a profile
- manage profile tags
- edit profile variables and cookies
- run a scenario for profiles matching a tag
- per-profile browser overrides:
  - locale
  - timezone
  - user agent
  - WebGL/GPU vendor
  - CPU cores

### Browser engine settings

- switch and configure Camoufox / CloakBrowser behavior
- headless/windowed execution settings
- humanization options
- OS fingerprint pool for Camoufox
- CloakBrowser fingerprint seed and Chromium launch options
- locale and timezone overrides
- persistent profile storage
- viewport and screen size defaults
- navigator, user agent, CPU and WebGL/GPU overrides
- Camoufox addons/fonts/exclude-addons settings

### Proxies

- proxy pools/groups
- bulk import proxy list
- supported input formats:
  - `socks5://host:port:user:password`
  - `http://user:pass@host:port`
- rename/delete pools
- edit/delete individual proxies
- select multiple proxies
- release or remove selected proxies
- health checks per proxy or group
- pool statistics: active, checking, failed, locations

### Scenarios

- visual node-based scenario editor (HTML canvas)
- draggable steps on a canvas
- pan/zoom canvas navigation
- success/error links between steps
- right-click context actions for nodes and links
- scenario library: create, duplicate, delete, save
- run selected scenario on a selected profile
- step editor with raw JSON preview

Supported step types:

- start / end
- open URL
- HTTP request
- wait for element
- wait for page load
- sleep
- click
- type text
- set variable
- parse variable
- pop from shared variables
- extract text
- write file
- compare / if
- open, switch and close browser tabs
- set tag
- run another scenario
- log/message

### Logs

- application and automation event log
- real-time log streaming via WebSocket
- refresh logs
- clear logs

### Settings

- application data root display
- UI theme selection

## Project structure

```text
app/
  core/              browser integration, fingerprints, proxies
  server.py           FastAPI server and REST API endpoints
  services/          scenario engine and executable steps
  static/            HTML/CSS/JS frontend (SPA)
  storage/           local database/storage helpers
  ui/http_app.py     entry point bootstrap (uvicorn + browser open)
  utils/             general helpers (logging, parsing)
docs-site/           Retype-based documentation (Markdown -> GH Pages)
images/              current screenshots used by README
scenaries/           example scenario JSON files
```

> The old `app/ui/bridge/`, `app/ui/tabs/`, `app/ui/qml_app.py`, and `app/qml/` directories contain the legacy PyQt6 UI layer and are no longer imported by the active code path.

## Requirements

- Python 3.12 recommended
- Git

Python dependencies are listed in `requirements.txt`:

- fastapi
- uvicorn[standard]
- websockets
- Camoufox
- CloakBrowser
- PySocks
- PyInstaller

## Install

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

First launch can take longer while browser dependencies are prepared.

## Run

```bat
python main.py
```

This starts the FastAPI server and opens your default browser to the app. The server runs on `http://127.0.0.1:8520` (or the next available port).

For development with auto-reload:

```bat
python -m uvicorn app.server:app --reload
```

Then open `http://127.0.0.1:8000` in your browser.

## Build Windows app

```bat
build.bat
```

Output:

```text
dist\CamouFlow\CamouFlow.exe
```

## Tests

There is no full automated test suite yet. For a quick static check:

```bat
python -m compileall app
```

## Data and storage

CamouFlow stores working data locally:

- profiles
- scenarios
- proxies
- settings
- logs
- browser profile data

The active data root is shown in **Settings**.

## License

MIT