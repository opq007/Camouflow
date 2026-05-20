"""Profiles bridge for QML."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtProperty, pyqtSignal, pyqtSlot

from app.core.browser_interface import BrowserInterface
from app.storage.db import db_add_account, db_delete_account, db_get_accounts, db_get_setting, db_update_account
from app.ui.bridge.models import DictListModel

LOGGER = logging.getLogger(__name__)


class ProfilesBridge(QObject):
    modelChanged = pyqtSignal()
    countsChanged = pyqtSignal()
    message = pyqtSignal(str)

    def __init__(self, app_state=None, parent=None) -> None:
        super().__init__(parent)
        self._model = DictListModel([
            "name", "id", "browser", "proxy", "lastActive", "status", "stage", "tags", "running"
        ], parent=self)
        self._stages_model = DictListModel(["name", "count", "selected"], parent=self)
        self._selected_stage = ""
        self._live_browsers: Dict[str, BrowserInterface] = {}
        self._app_state = app_state
        if app_state is not None:
            app_state.refreshRequested.connect(self.refresh)
        self.refresh()

    @pyqtProperty(QObject, constant=True)
    def model(self) -> QObject:
        return self._model

    @pyqtProperty(QObject, constant=True)
    def stagesModel(self) -> QObject:  # noqa: N802
        return self._stages_model

    @pyqtProperty(str, notify=modelChanged)
    def selectedStage(self) -> str:  # noqa: N802
        return self._selected_stage

    @pyqtProperty(int, notify=countsChanged)
    def total(self) -> int:
        return self._model.rowCount()

    @pyqtProperty(int, notify=countsChanged)
    def running(self) -> int:
        return len(self._live_browsers)

    def live_browsers(self) -> Dict[str, BrowserInterface]:
        return self._live_browsers

    def _emit_message(self, text: str) -> None:
        self.message.emit(text)
        if self._app_state is not None:
            self._app_state.notify(text)

    def _proxy_label(self, acc: Dict[str, Any]) -> str:
        host = str(acc.get("proxy_host") or "")
        port = acc.get("proxy_port")
        if host and port:
            return f"{host}:{port}"
        return str(acc.get("proxy_pool") or "None")

    @pyqtSlot()
    def refresh(self) -> None:
        rows: List[Dict[str, Any]] = []
        accounts = db_get_accounts()
        stage_counts: Dict[str, int] = {}
        for acc in accounts:
            stage_counts[str(acc.get("stage") or "No tag")] = stage_counts.get(str(acc.get("stage") or "No tag"), 0) + 1
        try:
            configured_stages = json.loads(db_get_setting("stages_json") or "[]")
        except Exception:
            configured_stages = []
        for stage in configured_stages if isinstance(configured_stages, list) else []:
            clean_stage = str(stage or "").strip()
            if clean_stage:
                stage_counts.setdefault(clean_stage, 0)
        self._stages_model.set_rows(
            [{"name": "All tags", "count": len(accounts), "selected": not self._selected_stage}]
            + [
                {"name": stage, "count": count, "selected": self._selected_stage == stage}
                for stage, count in sorted(stage_counts.items(), key=lambda item: item[0].lower())
            ]
        )
        sorted_accounts = sorted(accounts, key=lambda a: (str(a.get("stage") or "No tag").lower(), str(a.get("name") or "").lower()))
        for index, acc in enumerate(sorted_accounts, start=1):
            name = str(acc.get("name") or f"profile{index}")
            stage = str(acc.get("stage") or "")
            stage_label = stage or "No tag"
            if self._selected_stage and self._selected_stage != stage_label:
                continue
            running = name in self._live_browsers
            tags = []
            if stage:
                tags.append(stage)
            for key in ("tag", "type"):
                val = str(acc.get(key) or "")
                if val and val not in tags:
                    tags.append(val)
            engine = str(acc.get("_browser_engine") or acc.get("browser_engine") or "camoufox")
            if engine == "cloakbrowser":
                browser_label = "CloakBrowser"
            else:
                browser_label = "Camoufox"
            rows.append({
                "name": name,
                "id": str(acc.get("id") or f"#{index:04d}"),
                "browser": browser_label,
                "proxy": self._proxy_label(acc),
                "lastActive": str(acc.get("last_active") or "now" if running else acc.get("last_active") or "idle"),
                "status": "Running" if running else "Stopped",
                "stage": stage or "No tag",
                "tags": "  ".join(f"#{tag}" for tag in tags) if tags else "#profile",
                "running": running,
            })
        self._model.set_rows(rows)
        self.modelChanged.emit()
        self.countsChanged.emit()

    @pyqtSlot(str)
    def setStageFilter(self, stage: str) -> None:  # noqa: N802
        stage = str(stage or "")
        if stage == "All tags":
            stage = ""
        self._selected_stage = stage
        self.refresh()

    @pyqtSlot()
    def createProfile(self) -> None:  # noqa: N802
        existing = db_get_accounts()
        next_index = len(existing) + 1
        names = {str(acc.get("name") or "").lower() for acc in existing}
        while f"profile{next_index}".lower() in names:
            next_index += 1
        name = f"profile{next_index}"
        try:
            db_add_account({"name": name, "stage": ""})
        except Exception as exc:
            self._emit_message(f"Cannot create profile: {exc}")
            return
        self._emit_message(f"Profile {name} created")
        self.refresh()

    @pyqtSlot(str, str, result="QVariant")
    def getProfile(self, name: str, engine: str = "camoufox") -> Dict[str, Any]:  # noqa: N802
        target = str(name or "").strip()
        acc = next((item for item in db_get_accounts() if str(item.get("name") or "") == target), None)
        if not acc:
            return {}
        engine = str(engine or "camoufox").lower()
        settings_key = "cloakbrowser_settings" if engine == "cloakbrowser" else "camoufox_settings"
        settings = acc.get(settings_key)
        if isinstance(settings, str):
            try:
                import json

                parsed = json.loads(settings)
                settings = parsed if isinstance(parsed, dict) else {}
            except Exception:
                settings = {}
        if not isinstance(settings, dict):
            settings = {}
        return {
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
            "hardware_concurrency": "" if settings.get("hardware_concurrency") in (None, "", 0) else str(settings.get("hardware_concurrency")),
        }

    @pyqtSlot(str, str, str, str, str, str, str, str, str, str, str, str, str)
    def saveProfile(
        self,
        original_name: str,
        name: str,
        stage: str,
        proxy_host: str,
        proxy_port: str,
        proxy_user: str,
        proxy_password: str,
        engine: str,
        locale: str,
        timezone: str,
        user_agent: str,
        webgl_vendor: str,
        hardware_concurrency: str,
    ) -> None:  # noqa: N802
        original_name = str(original_name or "").strip()
        clean_name = str(name or "").strip()
        if not original_name or not clean_name:
            self._emit_message("Profile name is required")
            return
        updates: Dict[str, Any] = {
            "name": clean_name,
            "stage": str(stage or "").strip(),
            "proxy_host": str(proxy_host or "").strip(),
            "proxy_user": str(proxy_user or "").strip(),
            "proxy_password": str(proxy_password or "").strip(),
        }
        port_text = str(proxy_port or "").strip()
        if port_text:
            try:
                updates["proxy_port"] = int(port_text)
            except Exception:
                self._emit_message("Proxy port must be a number")
                return
        else:
            updates["proxy_port"] = None

        browser_settings: Dict[str, Any] = {}
        for key, value in {
            "locale": locale,
            "timezone": timezone,
            "user_agent": user_agent,
            "webgl_vendor": webgl_vendor,
            "gpu_vendor": webgl_vendor,
        }.items():
            value = str(value or "").strip()
            if value:
                browser_settings[key] = value
        cpu_text = str(hardware_concurrency or "").strip()
        if cpu_text:
            try:
                browser_settings["hardware_concurrency"] = int(cpu_text)
            except Exception:
                self._emit_message("CPU cores must be a number")
                return
        settings_key = "cloakbrowser_settings" if str(engine or "").lower() == "cloakbrowser" else "camoufox_settings"
        if browser_settings:
            updates[settings_key] = browser_settings
        else:
            updates["__delete_keys__"] = [settings_key]
        try:
            db_update_account(original_name, updates)
        except Exception as exc:
            self._emit_message(f"Cannot save profile: {exc}")
            return
        self._emit_message(f"Profile {clean_name} saved")
        self.refresh()

    @pyqtSlot(str)
    def deleteProfile(self, name: str) -> None:  # noqa: N802
        name = str(name or "").strip()
        if not name:
            return
        self.stopProfile(name)
        db_delete_account(name)
        self._emit_message(f"Profile {name} deleted")
        self.refresh()

    @pyqtSlot(str)
    def startProfile(self, name: str) -> None:  # noqa: N802
        name = str(name or "").strip()
        if not name or name in self._live_browsers:
            return
        acc = next((item for item in db_get_accounts() if str(item.get("name") or "") == name), None)
        if not acc:
            self._emit_message(f"Profile {name} not found")
            return
        proxy = self._proxy_for(acc)
        browser = BrowserInterface(profile_name=name, proxy=proxy, keep_browser_open=True)
        browser.add_close_callback(lambda: QTimer.singleShot(0, lambda: self._on_browser_closed(name, browser)))
        self._live_browsers[name] = browser
        self._emit_message(f"Starting browser for {name}")
        self.refresh()

        def worker() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(browser.start())
            except Exception as exc:
                LOGGER.exception("Browser start failed for %s", name)
                QTimer.singleShot(0, lambda exc=exc: self._on_browser_failed(name, browser, exc))
            finally:
                try:
                    loop.close()
                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()

    def _proxy_for(self, acc: Dict[str, Any]) -> str:
        host = str(acc.get("proxy_host") or "")
        port = acc.get("proxy_port")
        user = str(acc.get("proxy_user") or "")
        pwd = str(acc.get("proxy_password") or "")
        if not (host and port):
            return ""
        if user and pwd:
            return f"socks5://{host}:{port}:{user}:{pwd}"
        return f"socks5://{host}:{port}"

    def _on_browser_failed(self, name: str, browser: BrowserInterface, exc: Exception) -> None:
        if self._live_browsers.get(name) is browser:
            self._live_browsers.pop(name, None)
        self._emit_message(f"Cannot start {name}: {exc}")
        self.refresh()

    def _on_browser_closed(self, name: str, browser: BrowserInterface) -> None:
        if self._live_browsers.get(name) is browser:
            self._live_browsers.pop(name, None)
        self._emit_message(f"Browser closed for {name}")
        self.refresh()

    @pyqtSlot(str)
    def stopProfile(self, name: str) -> None:  # noqa: N802
        name = str(name or "").strip()
        browser = self._live_browsers.pop(name, None)
        if browser is None:
            self.refresh()
            return

        def worker() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(browser.close(force=True))
            except Exception:
                LOGGER.exception("Browser stop failed for %s", name)
            finally:
                loop.close()
                QTimer.singleShot(0, self.refresh)

        threading.Thread(target=worker, daemon=True).start()
        self._emit_message(f"Stopping browser for {name}")
        self.refresh()

    @pyqtSlot(str, str)
    def setStage(self, name: str, stage: str) -> None:  # noqa: N802
        try:
            db_update_account(str(name), {"stage": str(stage or "")})
            self.refresh()
        except Exception as exc:
            self._emit_message(f"Cannot update profile: {exc}")
