from __future__ import annotations
import atexit, logging, os, signal, socket, subprocess, sys, time
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

LOGGER = logging.getLogger(__name__)

# ---- helpers ----
def _is_linux():
    return sys.platform.startswith("linux")

def _which(cmd):
    try:
        subprocess.run(["which", cmd], capture_output=True, check=True)
        return True
    except Exception:
        return False

def _free_display_number(start=100):
    for n in range(start, start + 200):
        if not Path("/tmp/.X" + str(n) + "-lock").exists() and not Path("/tmp/.X11-unix/X" + str(n)).exists():
            return n
    raise RuntimeError("No free X display numbers (100-299)")

def _free_port(start, end):
    for p in range(start, end):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", p))
                return p
        except OSError:
            continue
    return 0

def _kill_xvfb(display_num):
    lock = Path("/tmp/.X" + str(display_num) + "-lock")
    try:
        if lock.exists():
            pid_bytes = lock.read_bytes()[:32]
            try: pid = int(pid_bytes.decode().strip())
            except Exception: pid = 0
            if pid > 1:
                try: os.kill(pid, signal.SIGTERM)
                except OSError: pass
    except Exception: pass
    for p in (lock, Path("/tmp/.X11-unix/X" + str(display_num))):
        try: p.unlink(missing_ok=True)
        except Exception: pass

class VirtualDisplayManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._linux = _is_linux()
        self._xvfb = self._linux and _which("Xvfb")
        self._xdpy = self._linux and _which("xdpyinfo")
        self._x11vnc = self._linux and _which("x11vnc")
        self._displays: Dict[str, Tuple[int, subprocess.Popen, int, int]] = {}
        # vnc_servers: profile_name -> (vnc_port, vnc_proc)
        self._vnc_servers: Dict[str, Tuple[int, subprocess.Popen]] = {}
        self._ws_servers: Dict[str, Tuple[int, subprocess.Popen]] = {}
        atexit.register(self.stop_all)

    @property
    def available(self):
        return self._xvfb

    @property
    def vnc_available(self):
        return self._x11vnc

    # ---- Xvfb ----
    def start(self, profile_name, width=1920, height=1080, depth=24):
        if not self._xvfb:
            return None
        if profile_name in self._displays:
            dnum, proc, _, _ = self._displays[profile_name]
            if proc and proc.poll() is None:
                return ":" + str(dnum)
            self.stop(profile_name)
        dnum = _free_display_number()
        LOGGER.info("Starting Xvfb :%d for %s (%dx%dx%d)", dnum, profile_name, width, height, depth)
        cmd = ["Xvfb", ":" + str(dnum), "-screen", "0", f"{width}x{height}x{depth}",
               "-ac", "+extension", "RANDR", "+extension", "RENDER",
               "-nolisten", "tcp", "-noreset"]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                env=dict(os.environ), start_new_session=True)
        disp = ":" + str(dnum)
        deadline = time.time() + 5.0
        while time.time() < deadline:
            if proc.poll() is not None:
                raise RuntimeError("Xvfb on " + disp + " exited (code " + str(proc.returncode) + ")")
            if self._xdpy:
                if subprocess.call(["xdpyinfo", "-display", disp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                    break
            elif Path("/tmp/.X" + str(dnum) + "-lock").exists():
                time.sleep(0.5)
                break
            time.sleep(0.3)
        else:
            proc.terminate()
            raise RuntimeError("Xvfb on " + disp + " not ready in 5s")
        self._displays[profile_name] = (dnum, proc, width, height)
        LOGGER.info("Virtual display :%d ready for %s", dnum, profile_name)
        return disp

    def stop(self, profile_name):
        self.stop_websockify(profile_name)
        self.stop_vnc(profile_name)
        entry = self._displays.pop(profile_name, None)
        if entry is None:
            return
        dnum, proc, _, _ = entry
        LOGGER.info("Stopping virtual display :%d for %s", dnum, profile_name)
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                try: proc.kill(); proc.wait(timeout=2)
                except Exception: pass
        _kill_xvfb(dnum)

    # ---- websockify ----
    def start_websockify(self, profile_name) -> Optional[int]:
        """Start a websockify bridge for the VNC server. Returns WS port or None."""
        try:
            import websockify
        except ImportError:
            LOGGER.warning("websockify not installed; browser VNC viewing unavailable")
            return None
        vnc_entry = self.vnc_info(profile_name)
        if not vnc_entry:
            return None
        vnc_port = vnc_entry["vnc_port"]
        ws_port = _free_port(6080, 6150)
        if not ws_port:
            return None

        LOGGER.info("Starting websockify for %s: WS %d -> VNC %d", profile_name, ws_port, vnc_port)
        cmd = [
            sys.executable, "-m", "websockify", "--web", "",
            str(ws_port), "127.0.0.1:" + str(vnc_port)
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                env=dict(os.environ), start_new_session=True)
        time.sleep(0.3)
        self._ws_servers[profile_name] = (ws_port, proc)
        LOGGER.info("websockify ready for %s on WS port %d", profile_name, ws_port)
        return ws_port

    def stop_websockify(self, profile_name):
        entry = self._ws_servers.pop(profile_name, None)
        if entry is None:
            return
        ws_port, proc = entry
        LOGGER.info("Stopping websockify on port %d for %s", ws_port, profile_name)
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                try: proc.kill(); proc.wait(timeout=2)
                except Exception: pass

    def stop_all(self):
        for name in list(self._displays.keys()):
            self.stop(name)

    def display_for(self, profile_name):
        entry = self._displays.get(profile_name)
        if entry is None:
            return None
        dnum, proc, _, _ = entry
        if proc is None or proc.poll() is not None:
            return None
        return ":" + str(dnum)

    # ---- x11vnc ----
    def start_vnc(self, profile_name) -> Optional[Dict[str, Any]]:
        if not self._x11vnc:
            return None
        display = self.display_for(profile_name)
        if not display:
            return None
        if profile_name in self._vnc_servers:
            vnc_port, proc = self._vnc_servers[profile_name]
            if proc and proc.poll() is None:
                return {"vnc_port": vnc_port, "display": display}
            self.stop_vnc(profile_name)

        vnc_port = _free_port(5901, 5950)
        if not vnc_port:
            LOGGER.warning("No free VNC port for %s", profile_name)
            return None

        LOGGER.info("Starting x11vnc on port %d for %s (display %s)", vnc_port, profile_name, display)
        cmd = [
            "x11vnc",
            "-display", display,
            "-rfbport", str(vnc_port),
            "-shared",
            "-forever",
            "-nopw",
            "-noshm",
            "-quiet",
            "-bg",
            "-xkb",
            "-ncache", "10",
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                env=dict(os.environ), start_new_session=True)
        time.sleep(0.5)
        self._vnc_servers[profile_name] = (vnc_port, proc)
        LOGGER.info("VNC server ready for %s on port %d", profile_name, vnc_port)
        return {"vnc_port": vnc_port, "display": display}

    def stop_vnc(self, profile_name):
        entry = self._vnc_servers.pop(profile_name, None)
        if entry is None:
            return
        vnc_port, proc = entry
        LOGGER.info("Stopping VNC server on port %d for %s", vnc_port, profile_name)
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                try: proc.kill(); proc.wait(timeout=2)
                except Exception: pass

    def vnc_info(self, profile_name):
        entry = self._vnc_servers.get(profile_name)
        if entry is None:
            return None
        vnc_port, proc = entry
        if proc is None or proc.poll() is not None:
            return None
        return {"vnc_port": vnc_port, "display": self.display_for(profile_name)}

_VDM = None
def get_virtual_display_manager():
    global _VDM
    if _VDM is None:
        _VDM = VirtualDisplayManager()
    return _VDM