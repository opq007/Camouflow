"""FastAPI server for the HTML CamouFlow UI."""

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

from app.core.virtual_display import get_virtual_display_manager
from app.storage.db import (
    CAMOUFOX_DEFAULTS,
    CLOAKBROWSER_DEFAULTS,
    db_add_account,
    db_delete_account,
    db_get_accounts,
    db_get_browser_engine,
    db_get_camoufox_defaults,
    db_get_cloakbrowser_defaults,
    db_get_setting,
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

# --- proxy pool assignment ---
_assigned_proxies: Dict[str, str] = {}  # profile_name -> proxy_value

def _csv_list(value: Any) -> List[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]

def _assigned_pool_proxy(pool_name: str, profile_name: str) -> str:
    global _assigned_proxies
    if profile_name in _assigned_proxies:
        return _assigned_proxies[profile_name]
    # Look up from pool data
    try:
        pools = json.loads(db_get_setting("proxy_pools") or "{}")
        pool = pools.get(pool_name)
        if isinstance(pool, dict):
            for px in (pool.get("proxies") or []):
                if isinstance(px, dict) and profile_name in _csv_list(px.get("assigned_to")):
                    val = str(px.get("value") or "")
                    if val:
                        _assigned_proxies[profile_name] = val
                        return val
    except Exception:
        pass
    return ""

def _assign_pool_proxy(pool_name: str, profile_name: str) -> Optional[str]:
    global _assigned_proxies
    try:
        pools = json.loads(db_get_setting("proxy_pools") or "{}")
        pool = pools.get(pool_name)
        if not isinstance(pool, dict):
            return None
        proxies = pool.get("proxies") or []
        for px in proxies:
            if isinstance(px, dict):
                val = str(px.get("value") or "")
                if val:
                    # Track assignment (comma-separated for multi-profile support)
                    assigned_list = _csv_list(px.get("assigned_to"))
                    if profile_name not in assigned_list:
                        assigned_list.append(profile_name)
                        px["assigned_to"] = ", ".join(assigned_list)
                    else:
                        px["assigned_to"] = ", ".join(assigned_list)
                    px["status"] = "in use"
                    _assigned_proxies[profile_name] = val
                    pool["proxies"] = proxies
                    db_set_setting("proxy_pools", json.dumps(pools, ensure_ascii=False))
                    return val
    except Exception:
        pass
    return None

def _release_pool_proxy(pool_name: str, profile_name: str) -> None:
    global _assigned_proxies
    _assigned_proxies.pop(profile_name, None)
    try:
        pools = json.loads(db_get_setting("proxy_pools") or "{}")
        pool = pools.get(pool_name)
        if isinstance(pool, dict):
            for px in (pool.get("proxies") or []):
                if isinstance(px, dict):
                    assigned_list = _csv_list(px.get("assigned_to"))
                    if profile_name in assigned_list:
                        assigned_list.remove(profile_name)
                        px["assigned_to"] = ", ".join(assigned_list)
                        if not assigned_list:
                            px["status"] = "idle"
                        pool["proxies"] = pool.get("proxies") or []
                        break
            db_set_setting("proxy_pools", json.dumps(pools, ensure_ascii=False))
    except Exception:
        pass

def _proxy_for(acc: Dict[str, Any]) -> str:
    # Priority: direct host/port, then proxy pool assignment
    scheme = str(acc.get("proxy_scheme") or "socks5").strip() or "socks5"
    host = str(acc.get("proxy_host") or "")
    port = acc.get("proxy_port")
    user = str(acc.get("proxy_user") or "")
    pwd = str(acc.get("proxy_password") or "")
    if host and port:
        if user and pwd:
            return f"{scheme}://{user}:{pwd}@{host}:{port}"
        return f"{scheme}://{host}:{port}"
    # Try proxy pool
    pool_name = str(acc.get("proxy_pool") or "")
    if pool_name:
        assigned = _assigned_pool_proxy(pool_name, str(acc.get("name") or ""))
        if assigned:
            return assigned
    return 

def _proxy_label(acc: Dict[str, Any]) -> str:
    host = str(acc.get("proxy_host") or "")
    port = acc.get("proxy_port")
    if host and port:
        return f"{host}:{port}"
    pool_name = str(acc.get("proxy_pool") or "")
    profile_name = str(acc.get("name") or "")
    if pool_name and profile_name:
        pool = _load_proxy_pools().get(pool_name)
        if isinstance(pool, dict):
            for idx, px in enumerate(pool.get("proxies") or [], start=1):
                if isinstance(px, dict) and profile_name in _csv_list(px.get("assigned_to")):
                    name = str(px.get("name") or f"Proxy #{idx}")
                    return f"{pool_name} / {name}"
    return pool_name or "None"

def _sync_profile_proxy(pool_name: str, proxy: Dict[str, Any]) -> None:
    value = str(proxy.get("value") or "")
    assigned = _csv_list(proxy.get("assigned_to"))
    if not value or not assigned:
        return
    for profile_name in assigned:
        _assigned_proxies[profile_name] = value
        db_update_account(profile_name, {"proxy_pool": pool_name})

def _assign_specific_proxy(pool_name: str, proxy_index: int, profile_name: str) -> None:
    pools = _load_proxy_pools()
    proxies = (pools.get(pool_name) or {}).get("proxies") or []
    if not profile_name or proxy_index < 0 or proxy_index >= len(proxies):
        return
    for idx, px in enumerate(proxies):
        if not isinstance(px, dict):
            continue
        assigned = [name for name in _csv_list(px.get("assigned_to")) if name != profile_name]
        if idx == proxy_index:
            assigned.append(profile_name)
        px["assigned_to"] = ", ".join(assigned)
        px["status"] = "in use" if assigned else "idle"
    db_set_setting("proxy_pools", json.dumps(pools, ensure_ascii=False))
    _sync_profile_proxy(pool_name, proxies[proxy_index])

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
        accounts = [a for a in accounts if stage in (_csv_list(a.get("stage")) or ["No tag"])]

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
            "proxy_pool": str(acc.get("proxy_pool") or ""),
            "lastActive": str(acc.get("last_active") or ("now" if running else "idle")),
            "status": "Running" if running else "Stopped",
            "stage": stage_val or "No tag",
            "running": running, "cdp_port": cdp_port, "cdp_url": f"http://127.0.0.1:{cdp_port}" if cdp_port else "", "vnc_port": (_live_browsers.get(name) or {}).get("vnc_port", 0), "ws_port": (_live_browsers.get(name) or {}).get("ws_port", 0),
        })
    return JSONResponse(rows)

@app.get("/api/profiles/stages")
def api_profiles_stages() -> JSONResponse:
    accounts = db_get_accounts()
    stage_counts: Dict[str, int] = {}
    for acc in accounts:
        for stage in (_csv_list(acc.get("stage")) or ["No tag"]):
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
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
        "proxy_scheme": str(acc.get("proxy_scheme") or "socks5"),
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
        "proxy_pool": str(acc.get("proxy_pool") or ""),
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
            account: Dict[str, Any] = {"name": name, "stage": default_stage, "proxy_pool": proxy_pool, "extra_fields": dict(parsed)}
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
        "proxy_scheme": str(data.get("proxy_scheme") or "socks5").strip(),
        "proxy_host": str(data.get("proxy_host") or "").strip(),
        "proxy_user": str(data.get("proxy_user") or "").strip(),
        "proxy_password": str(data.get("proxy_password") or "").strip(),
        "proxy_pool": str(data.get("proxy_pool") or "").strip(),
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
    _assigned_proxies.pop(name, None)
    _assigned_proxies.pop(clean_name, None)
    proxy_index = str(data.get("proxy_index") or "").strip()
    if updates["proxy_pool"] and proxy_index:
        try:
            _assign_specific_proxy(updates["proxy_pool"], int(proxy_index), clean_name)
        except Exception:
            return JSONResponse({"ok": False, "error": "Invalid proxy selection"}, 400)
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
        return JSONResponse({"ok": True, "status": "already_running", "cdp_port": cdp, "cdp_url": f"http://127.0.0.1:{cdp}" if cdp else "", "vnc_port": info.get("vnc_port", 0), "display": info.get("display", "")})
    acc = next((item for item in db_get_accounts() if str(item.get("name") or "") == name), None)
    if not acc:
        return JSONResponse({"ok": False, "error": "Profile not found"}, 404)
    proxy = _proxy_for(acc)
    # Auto-assign proxy from pool if profile has proxy_pool but no direct proxy
    pool = str(acc.get("proxy_pool") or "")
    if pool and not proxy:
        assigned = _assign_pool_proxy(pool, name)
        if assigned:
            proxy = assigned
            broadcast_log(f"Assigned proxy from pool {pool} to {name}")
    engine = str(acc.get("_browser_engine") or acc.get("browser_engine") or "camoufox")
    from app.core.browser_interface import BrowserInterface

    # Merge global browser defaults with profile-specific settings
    if engine == "cloakbrowser":
        global_defaults = dict(db_get_cloakbrowser_defaults() or CLOAKBROWSER_DEFAULTS)
    else:
        global_defaults = dict(db_get_camoufox_defaults() or CAMOUFOX_DEFAULTS)
    profile_settings = _settings_dict(acc.get("cloakbrowser_settings") if engine == "cloakbrowser" else acc.get("camoufox_settings"))
    settings = {**global_defaults, **(profile_settings or {})}
    if settings is None:
        settings = {}
    settings.setdefault("headless", False)
    # Cap window dimensions so browsers stay manageable
    w = settings.get("window_width", 0)
    h = settings.get("window_height", 0)
    if isinstance(w, (int, float)) and w > 1440:
        settings["window_width"] = 1440
    if isinstance(h, (int, float)) and h > 900:
        settings["window_height"] = 900

    # Allocate a CDP debugging port (skip ports already tracked in _live_browsers)
    used_ports = {info.get("cdp_port") for info in _live_browsers.values()}
    cdp_port = 0
    for port in range(9222, 9262):
        if port in used_ports:
            continue
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

    # Virtual display: start Xvfb if configured
    vdm = get_virtual_display_manager()
    display_str = ""
    vnc_info = None
    if vdm.available and settings.get("vd_enabled"):
        vd_w = int(settings.get("vd_width", 1920)) or 1920
        vd_h = int(settings.get("vd_height", 1080)) or 1080
        vd_d = int(settings.get("vd_depth", 24)) or 24
        try:
            display_str = vdm.start(name, width=vd_w, height=vd_h, depth=vd_d)
            if display_str:
                broadcast_log(f"Virtual display {display_str} started for {name}")
                # Start x11vnc for remote VNC viewing
                try:
                    vnc_info = vdm.start_vnc(name)
                    if vnc_info:
                        vnc_port_str = str(vnc_info.get('vnc_port', 0))
                        broadcast_log('VNC server for ' + name + ' on port ' + vnc_port_str)
                        # Start websockify bridge for browser-based viewing
                        try:
                            ws_port = vdm.start_websockify(name)
                            if ws_port:
                                vnc_info['ws_port'] = ws_port
                                broadcast_log('WebSocket for ' + name + ' on port ' + str(ws_port))
                        except Exception as exc:
                            broadcast_log('WebSocket start failed for ' + name + ': ' + str(exc))
                except Exception as exc:
                    broadcast_log('VNC start failed for ' + name + ': ' + str(exc))
        except Exception as exc:
            broadcast_log(f"Virtual display failed for {name}: {exc}")

    browser = BrowserInterface(profile_name=name, proxy=proxy, keep_browser_open=True,
                               browser_engine=engine, browser_settings=settings,
                               display=display_str or "")
    browser.add_close_callback(lambda: _on_browser_closed(name, browser))
    _live_browsers[name] = {"browser": browser, "cdp_port": cdp_port, "engine": engine, "display": display_str, "vnc_port": vnc_info.get("vnc_port", 0) if vnc_info else 0, "ws_port": vnc_info.get("ws_port", 0) if vnc_info else 0}
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
    return JSONResponse({"ok": True, "status": "starting", "cdp_port": cdp_port, "cdp_url": f"http://127.0.0.1:{cdp_port}" if cdp_port else "", "headless": False, "vnc_port": vnc_info.get("vnc_port") if vnc_info else 0, "display": display_str})
@app.post("/api/profiles/{name}/stop")
def api_profile_stop(name: str) -> JSONResponse:
    info = _live_browsers.get(name)
    if info is None:
        return JSONResponse({"ok": False, "error": "Not running"}, 404)
    browser = info.get("browser") if isinstance(info, dict) else info
    cdp_port = int((info.get("cdp_port") if isinstance(info, dict) else 0) or 0)
    if browser is None:
        return JSONResponse({"ok": False, "error": "Not running"}, 404)

    def worker() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        closed = False
        try:
            loop.run_until_complete(browser.close(force=True))
            closed = True
        except RuntimeError as exc:
            LOGGER.info("Browser %s close hit event-loop mismatch: %s", name, exc)
        except Exception:
            LOGGER.exception("Browser stop failed for %s", name)
        finally:
            if not closed:
                try:
                    closed = bool(browser.force_kill_profile_processes(cdp_port))
                except Exception:
                    LOGGER.exception("Browser force kill failed for %s", name)
            if not closed:
                broadcast_log(f"Cannot stop browser for {name}")
                _live_browsers[name] = info
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
    try:
        get_virtual_display_manager().stop(name)
    except Exception:
        pass
    try:
        accs = db_get_accounts()
        acc = next((a for a in accs if str(a.get("name") or "") == name), None)
        if acc:
            pool = str(acc.get("proxy_pool") or "")
            if pool:
                _assigned_proxies.pop(name, None)
    except Exception:
        pass
    broadcast_log(f"Cannot start {name}: {exc}")

def _on_browser_closed(name: str, browser: Any) -> None:
    if (b := _live_browsers.get(name)) and b.get("browser") is browser:
        _live_browsers.pop(name, None)
    try:
        get_virtual_display_manager().stop(name)
    except Exception:
        pass
    # Clear runtime proxy cache only; assigned_to is a persistent profile setting.
    try:
        accs = db_get_accounts()
        acc = next((a for a in accs if str(a.get("name") or "") == name), None)
        if acc:
            pool = str(acc.get("proxy_pool") or "")
            if pool:
                _assigned_proxies.pop(name, None)
    except Exception:
        pass
    broadcast_log(f"Browser closed for {name}")

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
        proxies.append({"name": f"Proxy #{len(proxies) + 1}", "value": line, "assigned_to": "", "status": "idle", "country": "", "region": "", "tags": ""})
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

@app.post("/api/proxies/pool/{name}/assign")
def api_proxy_assign(name: str, data: Dict[str, Any]) -> JSONResponse:
    idx = int(data.get("index", -1) if data.get("index") is not None else -1)
    profile = str(data.get("profile") or "").strip()
    profiles = _csv_list(data.get("profiles")) or _csv_list(profile)
    pools = _load_proxy_pools()
    if name not in pools:
        return JSONResponse({"ok": False, "error": "Pool not found"}, 404)
    proxies = pools[name].get("proxies") or []
    if idx < 0 or idx >= len(proxies):
        return JSONResponse({"ok": False, "error": "Invalid proxy index"}, 400)
    old_target = set(_csv_list(proxies[idx].get("assigned_to")))
    # Assign or release
    if profiles:
        # Check profile not already assigned to another proxy in this pool
        for i, px in enumerate(proxies):
            if i == idx:
                continue
            old_assigned = set(_csv_list(px.get("assigned_to")))
            assigned = [p for p in _csv_list(px.get("assigned_to")) if p not in profiles]
            for profile_name in old_assigned - set(assigned):
                _assigned_proxies.pop(profile_name, None)
            px["assigned_to"] = ", ".join(assigned)
            px["status"] = "in use" if assigned else "idle"
        for profile_name in old_target - set(profiles):
            _assigned_proxies.pop(profile_name, None)
        proxies[idx]["assigned_to"] = ", ".join(profiles)
        proxies[idx]["status"] = "in use"
        _sync_profile_proxy(name, proxies[idx])
        broadcast_log(f"Proxy {idx+1} in pool {name} assigned to {', '.join(profiles)}")
    else:
        for profile_name in _csv_list(proxies[idx].get("assigned_to")):
            _assigned_proxies.pop(profile_name, None)
        proxies[idx]["assigned_to"] = ""
        proxies[idx]["status"] = "idle"
        broadcast_log(f"Proxy {idx+1} in pool {name} released")
    pools[name]["proxies"] = proxies
    db_set_setting("proxy_pools", json.dumps(pools, ensure_ascii=False))
    return JSONResponse({"ok": True})

@app.put("/api/proxies/pool/{name}/proxies/{idx}")
def api_proxy_update(name: str, idx: int, data: Dict[str, Any]) -> JSONResponse:
    pools = _load_proxy_pools()
    if name not in pools:
        return JSONResponse({"ok": False, "error": "Pool not found"}, 404)
    proxies = pools[name].get("proxies") or []
    if idx < 0 or idx >= len(proxies):
        return JSONResponse({"ok": False, "error": "Invalid proxy index"}, 400)
    proxy = proxies[idx]
    if not isinstance(proxy, dict):
        return JSONResponse({"ok": False, "error": "Invalid proxy"}, 400)
    old_assigned = set(_csv_list(proxy.get("assigned_to")))
    for key in ("name", "value", "country", "region", "tags"):
        proxy[key] = str(data.get(key) or "").strip()
    proxy["assigned_to"] = ", ".join(_csv_list(data.get("assigned_to")))
    proxy["status"] = "in use" if proxy["assigned_to"] else "idle"
    for profile_name in old_assigned - set(_csv_list(proxy.get("assigned_to"))):
        _assigned_proxies.pop(profile_name, None)
    _sync_profile_proxy(name, proxy)
    pools[name]["proxies"] = proxies
    db_set_setting("proxy_pools", json.dumps(pools, ensure_ascii=False))
    broadcast_log(f"Proxy {idx+1} in pool {name} updated")
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
