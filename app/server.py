"""FastAPI server replacing the PyQt6/QML bridge layer."""

from __future__ import annotations

import asyncio
import json
import logging
import socket
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles


from app.storage.db import (
    CAMOUFOX_DEFAULTS,
    CLOAKBROWSER_DEFAULTS,
    Scenario,
    db_add_account,
    db_delete_account,
    db_delete_scenario,
    db_get_accounts,
    db_get_browser_engine,
    db_get_camoufox_defaults,
    db_get_cloakbrowser_defaults,
    db_get_scenario,
    db_get_scenario_path,
    db_get_scenarios,
    db_get_setting,
    db_save_scenario,
    db_set_browser_engine,
    db_set_camoufox_defaults,
    db_set_cloakbrowser_defaults,
    db_set_setting,
    db_update_account,
)
# dashboard_data imported lazily
from app.utils.parsing import DEFAULT_ACCOUNT_TEMPLATE, parse_account_line

LOGGER = logging.getLogger(__name__)

app = FastAPI(title="CamouFlow")

# --- Log streaming state ---
_log_clients: List[WebSocket] = []
_log_messages: List[str] = []
_log_queue: List[str] = []
_loop: asyncio.AbstractEventLoop | None = None


def _install_loop() -> None:
    """Capture the running event loop for thread-safe log broadcasting."""
    global _loop
    try:
        _loop = asyncio.get_running_loop()
    except RuntimeError:
        pass


async def _flush_log_queue() -> None:
    """Coroutine that runs on the event loop to send queued messages."""
    while True:
        await asyncio.sleep(0.1)
        if not _log_queue:
            continue
        batch = _log_queue[:]
        _log_queue.clear()
        dead: List[WebSocket] = []
        for ws in _log_clients:
            for msg in batch:
                try:
                    await ws.send_text(msg)
                except Exception:
                    dead.append(ws)
                    break
        for ws in dead:
            if ws in _log_clients:
                _log_clients.remove(ws)


def broadcast_log(message: str) -> None:
    _log_messages.append(message)
    if len(_log_messages) > 1000:
        _log_messages[:] = _log_messages[-500:]
    _log_queue.append(message)
    if _loop is not None:
        _loop.call_soon_threadsafe(lambda: None)  # wake the loop

# --- Live browser tracking ---
_live_browsers: Dict[str, Any] = {}  # name -> {browser, cdp_port, engine}

def _proxy_for(acc: Dict[str, Any]) -> str:
    scheme = str(acc.get("proxy_scheme") or "socks5").strip() or "socks5"
    host = str(acc.get("proxy_host") or "")
    port = acc.get("proxy_port")
    user = str(acc.get("proxy_user") or "")
    pwd = str(acc.get("proxy_password") or "")
    if not (host and port):
        return ""
    if user and pwd:
        return f"{scheme}://{user}:{pwd}@{host}:{port}"
    return f"{scheme}://{host}:{port}"

def _proxy_label(acc: Dict[str, Any]) -> str:
    host = str(acc.get("proxy_host") or "")
    port = acc.get("proxy_port")
    if host and port:
        return f"{host}:{port}"
    return str(acc.get("proxy_pool") or "None")

def _settings_dict(value: Any) -> Optional[Dict[str, Any]]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None
    return None

# ============================================================
# WebSocket for log streaming
# ============================================================

@app.websocket("/api/logs/stream")
async def log_stream(ws: WebSocket) -> None:
    await ws.accept()
    _log_clients.append(ws)
    # Replay recent messages
    for msg in _log_messages[-50:]:
        try:
            await ws.send_text(msg)
        except Exception:
            break
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        if ws in _log_clients:
            _log_clients.remove(ws)

# ============================================================
# Dashboard
# ============================================================

@app.get("/api/dashboard")
def api_dashboard() -> JSONResponse:
    from app.ui.dashboard_data import build_dashboard_metrics, recent_log_lines
    metrics = build_dashboard_metrics(
        db_get_accounts(),
        db_get_scenarios(),
        _load_proxy_pools(),
        _live_browsers,
    )
    activity = recent_log_lines("\n".join(_log_messages), 7)
    return JSONResponse({"metrics": metrics, "activity": activity})

# ============================================================
# Profiles
# ============================================================

@app.get("/api/profiles")
def api_profiles_list(stage: str = "") -> JSONResponse:
    accounts = db_get_accounts()
    if stage and stage != "All tags":
        accounts = [a for a in accounts if str(a.get("stage") or "No tag") == stage]

    rows = []
    for idx, acc in enumerate(accounts, start=1):
        name = str(acc.get("name") or f"profile{idx}")
        running = name in _live_browsers
        cdp_port = (_live_browsers.get(name) or {}).get("cdp_port")
        stage_val = str(acc.get("stage") or "")
        engine = str(acc.get("_browser_engine") or acc.get("browser_engine") or "camoufox")
        if engine == "cloakbrowser":
            browser_label = "CloakBrowser"
        else:
            browser_label = "Camoufox"
        rows.append({
            "name": name,
            "id": str(acc.get("id") or f"#{idx:04d}"),
            "browser": browser_label,
            "proxy": _proxy_label(acc),
            "lastActive": str(acc.get("last_active") or ("now" if running else "idle")),
            "status": "Running" if running else "Stopped",
            "stage": stage_val or "No tag",
            "running": running, "cdp_port": cdp_port, "cdp_url": f"http://127.0.0.1:{cdp_port}" if cdp_port else "",
        })
    return JSONResponse(rows)

@app.get("/api/profiles/stages")
def api_profiles_stages() -> JSONResponse:
    accounts = db_get_accounts()
    stage_counts: Dict[str, int] = {}
    for acc in accounts:
        stage_counts[str(acc.get("stage") or "No tag")] = stage_counts.get(str(acc.get("stage") or "No tag"), 0) + 1
    return JSONResponse([
        {"name": stage, "count": count}
        for stage, count in sorted(stage_counts.items(), key=lambda x: x[0].lower())
    ])

@app.post("/api/profiles/create")
def api_profile_create() -> JSONResponse:
    existing = db_get_accounts()
    next_index = len(existing) + 1
    names = {str(acc.get("name") or "").lower() for acc in existing}
    while f"profile{next_index}".lower() in names:
        next_index += 1
    name = f"profile{next_index}"
    db_add_account({"name": name, "stage": ""})
    broadcast_log(f"Profile {name} created")
    return JSONResponse({"ok": True, "name": name})

@app.get("/api/profiles/{name}")
def api_profile_get(name: str, engine: str = "camoufox") -> JSONResponse:
    acc = next((item for item in db_get_accounts() if str(item.get("name") or "") == name), None)
    if not acc:
        return JSONResponse({}, 404)
    settings_key = "cloakbrowser_settings" if engine == "cloakbrowser" else "camoufox_settings"
    settings = acc.get(settings_key)
    if isinstance(settings, str):
        try:
            settings = json.loads(settings)
        except Exception:
            settings = {}
    if not isinstance(settings, dict):
        settings = {}
    return JSONResponse({
        "name": str(acc.get("name") or ""),
        "stage": str(acc.get("stage") or ""),
        "proxy_host": str(acc.get("proxy_host") or ""),
        "proxy_port": "" if acc.get("proxy_port") in (None, "") else str(acc.get("proxy_port")),
        "proxy_user": str(acc.get("proxy_user") or ""),
        "proxy_password": str(acc.get("proxy_password") or ""),
        "locale": str(settings.get("locale") or ""),
        "timezone": str(settings.get("timezone") or ""),
        "user_agent": str(settings.get("user_agent") or ""),
        "webgl_vendor": str(settings.get("webgl_vendor") or settings.get("gpu_vendor") or ""),
        "hardware_concurrency": settings.get("hardware_concurrency"),
        "engine": str(acc.get("_browser_engine") or acc.get("browser_engine") or "camoufox"),
    })

@app.post("/api/profiles/import")
def api_profile_import(data: Dict[str, Any]) -> JSONResponse:
    lines_raw = str(data.get("lines") or "")
    template = str(data.get("template") or DEFAULT_ACCOUNT_TEMPLATE)
    default_stage = str(data.get("stage") or "")
    proxy_pool = str(data.get("proxy_pool") or "")
    raw_lines = [line.strip() for line in lines_raw.replace("\r", "\n").split("\n") if line.strip()]
    if not raw_lines:
        return JSONResponse({"ok": False, "error": "Import list is empty"}, 400)
    added = 0
    errors = 0
    for line in raw_lines:
        try:
            parsed = parse_account_line(line, template)
            name = str(parsed.get("name") or parsed.get("email") or "").strip()
            if not name:
                name = f"profile{len(db_get_accounts()) + 1}"
            account: Dict[str, Any] = {"name": name, "stage": default_stage, "extra_fields": dict(parsed)}
            for key, value in parsed.items():
                account[str(key)] = str(value)
            db_add_account(account)
            added += 1
        except Exception:
            errors += 1
    broadcast_log(f"Imported {added} profile(s)" + (f", {errors} failed" if errors else ""))
    return JSONResponse({"ok": True, "added": added, "errors": errors})

@app.put("/api/profiles/{name}")
def api_profile_save(name: str, data: Dict[str, Any]) -> JSONResponse:
    clean_name = str(data.get("name") or name).strip()
    if not clean_name:
        return JSONResponse({"ok": False, "error": "Profile name is required"}, 400)
    updates: Dict[str, Any] = {
        "name": clean_name,
        "stage": str(data.get("stage") or "").strip(),
        "_browser_engine": str(data.get("engine") or "camoufox").lower(),
        "proxy_host": str(data.get("proxy_host") or "").strip(),
        "proxy_user": str(data.get("proxy_user") or "").strip(),
        "proxy_password": str(data.get("proxy_password") or "").strip(),
    }
    port_text = str(data.get("proxy_port") or "").strip()
    if port_text:
        try:
            updates["proxy_port"] = int(port_text)
        except Exception:
            return JSONResponse({"ok": False, "error": "Proxy port must be a number"}, 400)
    else:
        updates["proxy_port"] = None

    browser_settings: Dict[str, Any] = {}
    for key, field in (("locale", "locale"), ("timezone", "timezone"), ("user_agent", "user_agent"),
                       ("webgl_vendor", "webgl_vendor"), ("gpu_vendor", "webgl_vendor")):
        val = str(data.get(field) or "").strip()
        if val:
            browser_settings[key] = val
    cpu_text = str(data.get("hardware_concurrency") or "").strip()
    if cpu_text:
        try:
            browser_settings["hardware_concurrency"] = int(cpu_text)
        except Exception:
            return JSONResponse({"ok": False, "error": "CPU cores must be a number"}, 400)
    engine = str(data.get("engine") or "camoufox").lower()
    settings_key = "cloakbrowser_settings" if engine == "cloakbrowser" else "camoufox_settings"
    if browser_settings:
        updates[settings_key] = browser_settings
    else:
        updates["__delete_keys__"] = [settings_key]
    db_update_account(name, updates)
    broadcast_log(f"Profile {clean_name} saved")
    return JSONResponse({"ok": True})

@app.delete("/api/profiles/{name}")
def api_profile_delete(name: str) -> JSONResponse:
    api_profile_stop(name)
    db_delete_account(name)
    broadcast_log(f"Profile {name} deleted")
    return JSONResponse({"ok": True})

@app.post("/api/profiles/{name}/start")
def api_profile_start(name: str) -> JSONResponse:
    if name in _live_browsers:
        info = _live_browsers[name]
        cdp = info.get("cdp_port")
        return JSONResponse({"ok": True, "status": "already_running", "cdp_port": cdp, "cdp_url": f"http://127.0.0.1:{cdp}" if cdp else ""})
    acc = next((item for item in db_get_accounts() if str(item.get("name") or "") == name), None)
    if not acc:
        return JSONResponse({"ok": False, "error": "Profile not found"}, 404)
    proxy = _proxy_for(acc)
    engine = str(acc.get("_browser_engine") or acc.get("browser_engine") or "camoufox")
    from app.core.browser_interface import BrowserInterface

    settings = _settings_dict(acc.get("cloakbrowser_settings") if engine == "cloakbrowser" else acc.get("camoufox_settings"))
    if settings is None:
        settings = {}
    settings.setdefault("headless", False)

    # Allocate a CDP debugging port
    cdp_port = 0
    for port in range(9222, 9262):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                cdp_port = port
                break
        except OSError:
            continue
    if cdp_port > 0:
        launch_args = list(settings.get("launch_args") or [])
        remote_flag = f"--remote-debugging-port={cdp_port}"
        if not any(a.startswith("--remote-debugging-port=") for a in launch_args):
            launch_args.append(remote_flag)
        settings["launch_args"] = launch_args

    browser = BrowserInterface(profile_name=name, proxy=proxy, keep_browser_open=True,
                               browser_engine=engine, browser_settings=settings)
    browser.add_close_callback(lambda: _on_browser_closed(name, browser))
    _live_browsers[name] = {"browser": browser, "cdp_port": cdp_port, "engine": engine}
    broadcast_log(f"Starting browser for {name} (CDP port {cdp_port})")

    def worker() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(browser.start())
        except Exception as exc:
            LOGGER.exception("Browser start failed for %s", name)
            _on_browser_failed(name, browser, exc)
        finally:
            try:
                loop.close()
            except Exception:
                pass

    threading.Thread(target=worker, daemon=True).start()
    return JSONResponse({"ok": True, "status": "starting", "cdp_port": cdp_port, "cdp_url": f"http://127.0.0.1:{cdp_port}" if cdp_port else "", "headless": False})
@app.post("/api/profiles/{name}/stop")
def api_profile_stop(name: str) -> JSONResponse:
    info = _live_browsers.pop(name, None)
    if info is None:
        return JSONResponse({"ok": False, "error": "Not running"}, 404)
    browser = info.get("browser") if isinstance(info, dict) else info
    if browser is None:
        return JSONResponse({"ok": False, "error": "Not running"}, 404)

    def worker() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(browser.close(force=True))
        except RuntimeError:
            LOGGER.info("Browser %s already closed (event-loop mismatch)", name)
        except Exception:
            LOGGER.exception("Browser stop failed for %s", name)
        finally:
            loop.close()

    threading.Thread(target=worker, daemon=True).start()
    broadcast_log(f"Stopping browser for {name}")
    return JSONResponse({"ok": True})
def api_profile_variables(name: str) -> JSONResponse:
    acc = next((item for item in db_get_accounts() if str(item.get("name") or "") == name), None)
    if not acc:
        return JSONResponse({}, 404)
    hidden = {"id", "stage", "proxy_host", "proxy_port", "proxy_user", "proxy_password",
              "proxy_scheme", "proxy_pool", "camoufox_settings", "cloakbrowser_settings",
              "_browser_engine", "browser_engine", "last_active"}
    variables: Dict[str, Any] = {}
    extra = acc.get("extra_fields")
    if isinstance(extra, dict):
        variables.update(extra)
    for key, value in acc.items():
        if key not in hidden and key != "extra_fields":
            variables[str(key)] = value
    return JSONResponse(variables)

@app.put("/api/profiles/{name}/variables")
def api_profile_variables_save(name: str, data: Dict[str, Any]) -> JSONResponse:
    updates = {"extra_fields": data}
    for key, value in data.items():
        if str(key) == "name":
            continue
        updates[str(key)] = value
    db_update_account(name, updates)
    broadcast_log(f"Variables saved for {name}")
    return JSONResponse({"ok": True})

def _on_browser_failed(name: str, browser: Any, exc: Exception) -> None:
    if (b := _live_browsers.get(name)) and b.get("browser") is browser:
        _live_browsers.pop(name, None)
    broadcast_log(f"Cannot start {name}: {exc}")

def _on_browser_closed(name: str, browser: Any) -> None:
    if (b := _live_browsers.get(name)) and b.get("browser") is browser:
        _live_browsers.pop(name, None)
    broadcast_log(f"Browser closed for {name}")

# ============================================================
# Scenarios
# ============================================================

ACTION_OPTIONS = [
    ("Start scenario", "start"), ("Open URL", "goto"), ("HTTP request", "http_request"),
    ("Wait for element", "wait_element"), ("Wait for page load", "wait_for_load_state"),
    ("Sleep", "sleep"), ("Click element", "click"), ("Type text", "type"),
    ("Set variable", "set_var"), ("Parse variable", "parse_var"), ("Pop from shared", "pop_shared"),
    ("Extract text", "extract_text"), ("Write to file", "write_file"),
    ("Compare / if", "compare"), ("Open new tab", "new_tab"), ("Switch tab", "switch_tab"),
    ("Close tab", "close_tab"), ("Set tag", "set_tag"), ("Close browser", "end"),
    ("Run another scenario", "run_scenario"), ("Log / message", "log"),
]
ACTION_LABELS = {value: label for label, value in ACTION_OPTIONS}
ACTION_CATEGORIES = [
    ("Navigation & interaction", ["goto", "wait_for_load_state", "wait_element", "sleep", "click", "type"]),
    ("Variables", ["set_var", "parse_var", "pop_shared", "extract_text", "write_file"]),
    ("Network", ["http_request"]),
    ("Browser tabs", ["new_tab", "switch_tab", "close_tab"]),
    ("Flow & logging", ["start", "end", "run_scenario", "log", "set_tag", "compare"]),
]

@app.get("/api/scenarios")
def api_scenarios_list() -> JSONResponse:
    scenarios = db_get_scenarios()
    return JSONResponse([
        {"name": s.name, "description": s.description or "", "steps": len(s.steps or [])}
        for s in scenarios
    ])

@app.get("/api/scenarios/actions")
def api_scenario_actions() -> JSONResponse:
    return JSONResponse({
        "options": [{"label": l, "value": v} for l, v in ACTION_OPTIONS],
        "categories": [{"name": n, "actions": a} for n, a in ACTION_CATEGORIES],
    })

@app.get("/api/scenarios/{name}")
def api_scenario_get(name: str) -> JSONResponse:
    scenario = db_get_scenario(name)
    if not scenario:
        return JSONResponse({}, 404)
    steps = scenario.steps or []
    result = []
    for idx, step in enumerate(steps):
        action = str(step.get("action") or "")
        result.append({
            "index": idx,
            "action": action,
            "label": ACTION_LABELS.get(action, action),
            "tag": str(step.get("tag") or ""),
            "nextOk": str(step.get("next_success_step") or ""),
            "nextErr": str(step.get("next_error_step") or ""),
            "selector": str(step.get("selector") or ""),
            "selector_type": str(step.get("selector_type") or ""),
            "value": str(step.get("value") or ""),
            "url": str(step.get("url") or ""),
            "timeout_ms": step.get("timeout_ms"),
            "seconds": step.get("seconds"),
            "_pos": step.get("_pos"),
            "extra": json.dumps({k: v for k, v in step.items() if k not in {
                "action", "label", "tag", "next_success_step", "next_error_step",
                "selector", "selector_type", "value", "url", "timeout_ms", "seconds", "_pos"
            }}, ensure_ascii=False, indent=2),
        })
    return JSONResponse({
        "name": scenario.name,
        "description": scenario.description or "",
        "steps": result,
    })

@app.post("/api/scenarios/create")
def api_scenario_create() -> JSONResponse:
    base = "New scenario"
    existing = {s.name.lower() for s in db_get_scenarios()}
    name = base
    idx = 2
    while name.lower() in existing:
        name = f"{base} {idx}"
        idx += 1
    db_save_scenario(name, [{"action": "start", "tag": "Start"}], "")
    broadcast_log(f"Scenario {name} created")
    return JSONResponse({"ok": True, "name": name})

@app.put("/api/scenarios/{name}")
def api_scenario_save(name: str, data: Dict[str, Any]) -> JSONResponse:
    new_name = str(data.get("name") or name).strip() or name
    description = str(data.get("description") or "")
    steps = data.get("steps") or []
    if not isinstance(steps, list):
        steps = []
    db_save_scenario(new_name, steps, description)
    if name != new_name:
        db_delete_scenario(name)
    broadcast_log(f"Scenario {new_name} saved")
    return JSONResponse({"ok": True, "name": new_name})

@app.delete("/api/scenarios/{name}")
def api_scenario_delete(name: str) -> JSONResponse:
    db_delete_scenario(name)
    broadcast_log(f"Scenario {name} deleted")
    return JSONResponse({"ok": True})

@app.post("/api/scenarios/{name}/duplicate")
def api_scenario_duplicate(name: str) -> JSONResponse:
    scenario = db_get_scenario(name)
    if not scenario:
        return JSONResponse({"ok": False}, 404)
    base = f"{name} copy"
    existing = {s.name.lower() for s in db_get_scenarios()}
    new_name = base
    idx = 2
    while new_name.lower() in existing:
        new_name = f"{base} {idx}"
        idx += 1
    import copy
    steps = copy.deepcopy(scenario.steps or [])
    db_save_scenario(new_name, steps, scenario.description or "")
    broadcast_log(f"Scenario duplicated as {new_name}")
    return JSONResponse({"ok": True, "name": new_name})

@app.post("/api/scenarios/{name}/run")
def api_scenario_run(name: str, data: Dict[str, Any] = {}) -> JSONResponse:
    profile = str(data.get("profile") or "").strip()
    max_accounts = int(data.get("max_accounts") or 1)
    tag = str(data.get("tag") or "").strip()
    scenario = db_get_scenario(name)
    if not scenario:
        return JSONResponse({"ok": False, "error": "Scenario not found"}, 404)
    all_accounts = db_get_accounts()
    if profile:
        accounts = [a for a in all_accounts if str(a.get("name") or "") == profile]
    elif tag and tag != "All tags":
        accounts = [a for a in all_accounts if str(a.get("stage") or "No tag") == tag]
    else:
        accounts = all_accounts[:max_accounts]
    if not accounts:
        return JSONResponse({"ok": False, "error": "No profiles to run"}, 400)

    def worker() -> None:
        try:
            processed = run_scenario(accounts, scenario, max_accounts=min(max_accounts, len(accounts)),
                                     scenario_path=db_get_scenario_path(scenario.name))
            broadcast_log(f"Scenario finished: {len(processed)} profile(s)")
        except Exception as exc:
            LOGGER.exception("Scenario run failed")
            broadcast_log(f"Scenario failed: {exc}")

    broadcast_log(f"Running {scenario.name}")
    threading.Thread(target=worker, daemon=True).start()
    return JSONResponse({"ok": True})

# ============================================================
# Proxies
# ============================================================

def _load_proxy_pools() -> Dict[str, Any]:
    try:
        return json.loads(db_get_setting("proxy_pools") or "{}")
    except Exception:
        return {}

@app.get("/api/proxies")
def api_proxies_list() -> JSONResponse:
    pools = _load_proxy_pools()
    result = []
    for pool_name, pool_data in pools.items():
        if not isinstance(pool_data, dict):
            continue
        proxies = pool_data.get("proxies") or []
        result.append({"name": pool_name, "count": len(proxies), "proxies": proxies})
    return JSONResponse(result)

@app.post("/api/proxies/pool")
def api_proxy_pool_create(data: Dict[str, Any]) -> JSONResponse:
    name = str(data.get("name") or "").strip()
    if not name:
        return JSONResponse({"ok": False, "error": "Pool name is required"}, 400)
    pools = _load_proxy_pools()
    if name in pools:
        return JSONResponse({"ok": False, "error": "Pool already exists"}, 400)
    pools[name] = {"proxies": [], "created": ""}
    db_set_setting("proxy_pools", json.dumps(pools, ensure_ascii=False))
    broadcast_log(f"Proxy pool {name} created")
    return JSONResponse({"ok": True})

@app.delete("/api/proxies/pool/{name}")
def api_proxy_pool_delete(name: str) -> JSONResponse:
    pools = _load_proxy_pools()
    if name not in pools:
        return JSONResponse({"ok": False}, 404)
    del pools[name]
    db_set_setting("proxy_pools", json.dumps(pools, ensure_ascii=False))
    broadcast_log(f"Proxy pool {name} deleted")
    return JSONResponse({"ok": True})

@app.post("/api/proxies/pool/{name}/import")
def api_proxy_pool_import(name: str, data: Dict[str, Any]) -> JSONResponse:
    lines = str(data.get("lines") or "").strip()
    if not lines:
        return JSONResponse({"ok": False, "error": "No proxy data"}, 400)
    pools = _load_proxy_pools()
    if name not in pools:
        return JSONResponse({"ok": False, "error": "Pool not found"}, 404)
    pool = pools[name]
    proxies = pool.get("proxies") or []
    existing = {str(p.get("value") or "").strip() for p in proxies if isinstance(p, dict)}
    added = 0
    for line in lines.replace("\r", "\n").split("\n"):
        line = line.strip()
        if not line or line in existing:
            continue
        proxies.append({"value": line, "assigned_to": "", "status": "idle"})
        existing.add(line)
        added += 1
    pool["proxies"] = proxies
    db_set_setting("proxy_pools", json.dumps(pools, ensure_ascii=False))
    broadcast_log(f"Imported {added} proxies to {name}")
    return JSONResponse({"ok": True, "added": added})

@app.post("/api/proxies/pool/{name}/proxies/delete")
def api_proxy_delete(name: str, data: Dict[str, Any]) -> JSONResponse:
    indices = data.get("indices") or []
    pools = _load_proxy_pools()
    if name not in pools:
        return JSONResponse({"ok": False}, 404)
    proxies = pools[name].get("proxies") or []
    for idx in sorted(indices, reverse=True):
        if 0 <= idx < len(proxies):
            proxies.pop(idx)
    pools[name]["proxies"] = proxies
    db_set_setting("proxy_pools", json.dumps(pools, ensure_ascii=False))
    return JSONResponse({"ok": True})

# ============================================================
# Browser settings
# ============================================================

@app.get("/api/browser")
def api_browser_get() -> JSONResponse:
    engine = db_get_browser_engine()
    if engine == "cloakbrowser":
        defaults = dict(db_get_cloakbrowser_defaults() or CLOAKBROWSER_DEFAULTS)
    else:
        defaults = dict(db_get_camoufox_defaults() or CAMOUFOX_DEFAULTS)
    defaults["browser_engine"] = engine
    return JSONResponse(defaults)

@app.put("/api/browser")
def api_browser_save(data: Dict[str, Any]) -> JSONResponse:
    engine = str(data.get("browser_engine") or "camoufox").lower()
    db_set_browser_engine(engine)
    if engine == "cloakbrowser":
        db_set_cloakbrowser_defaults(data)
    else:
        db_set_camoufox_defaults(data)
    broadcast_log("Browser settings saved")
    return JSONResponse({"ok": True})

@app.post("/api/browser/reset")
def api_browser_reset() -> JSONResponse:
    engine = db_get_browser_engine()
    if engine == "cloakbrowser":
        db_set_cloakbrowser_defaults(dict(CLOAKBROWSER_DEFAULTS))
    else:
        db_set_camoufox_defaults(dict(CAMOUFOX_DEFAULTS))
    broadcast_log("Browser settings restored to defaults")
    return JSONResponse({"ok": True})

# ============================================================
# Logs
# ============================================================

@app.get("/api/logs")
def api_logs_get() -> JSONResponse:
    return JSONResponse(_log_messages[-200:])

@app.post("/api/logs/clear")
def api_logs_clear() -> JSONResponse:
    _log_messages.clear()
    return JSONResponse({"ok": True})

# ============================================================
# Settings
# ============================================================

@app.get("/api/settings")
def api_settings_get() -> JSONResponse:
    return JSONResponse({
        "data_root": str(db_get_setting("data_root") or ""),
        "ui_theme": str(db_get_setting("ui_theme") or "premium_dark"),
        "account_parse_template": str(db_get_setting("account_parse_template") or DEFAULT_ACCOUNT_TEMPLATE),
    })

@app.put("/api/settings")
def api_settings_save(data: Dict[str, Any]) -> JSONResponse:
    for key, value in data.items():
        db_set_setting(str(key), str(value))
    broadcast_log("Settings saved")
    return JSONResponse({"ok": True})

# ============================================================
# State
# ============================================================

@app.get("/api/state")
def api_state() -> JSONResponse:
    return JSONResponse({
        "version": "2.0.0",
        "running_browsers": len(_live_browsers),
    })

# ============================================================
# Static files (must be last)
# ============================================================

def mount_static(static_dir: Path) -> None:
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

# Auto-mount static files if they exist (for dev convenience with uvicorn directly)
_auto_static = Path(__file__).resolve().parent / "static"
if _auto_static.exists() and not any(r.path == "/" for r in app.routes):
    app.mount("/", StaticFiles(directory=str(_auto_static), html=True), name="static")
