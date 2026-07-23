import logging
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.browser_interface import BrowserInterface
from app.core.proxy_utils import ProxyDetails, parse_proxy
from app.storage.db import CLOAKBROWSER_DEFAULTS


class WebRTCLaunchOptionsTests(unittest.TestCase):
    def test_geo_response_ip_accepts_only_valid_ip(self):
        self.assertEqual(
            BrowserInterface._geo_response_ip({"ip": "203.0.113.10"}),
            "203.0.113.10",
        )
        self.assertEqual(
            BrowserInterface._geo_response_ip({"query": "2001:db8::1"}),
            "2001:db8::1",
        )
        self.assertEqual(BrowserInterface._geo_response_ip({"ip": "not an ip"}), "")

    def _make_cloakbrowser_shell(self, proxy_config=None, proxy_details=None):
        browser = BrowserInterface.__new__(BrowserInterface)
        browser.profile_name = "test-profile"
        browser.profile_root = Path("tmp")
        browser._browser_settings = {}
        browser._cloakbrowser_defaults = dict(
            CLOAKBROWSER_DEFAULTS,
            locale="en-US",
            timezone="UTC",
            fingerprint_seed=12345,
        )
        browser._proxy_config = proxy_config
        browser._proxy_details = proxy_details
        browser._local_proxy = None
        browser._proxy_logger = logging.LoggerAdapter(logging.getLogger("proxy_log"), {"profile": "test"})
        return browser

    def test_cloakbrowser_proxy_adds_webrtc_auto_arg_once(self):
        browser = self._make_cloakbrowser_shell(proxy_config={"server": "http://proxy.example:8080"})

        kwargs = browser._build_cloakbrowser_launch_kwargs()

        self.assertIn("--fingerprint-webrtc-ip=auto", kwargs["args"])

        browser._browser_settings = {"launch_args": ["--fingerprint-webrtc-ip=198.51.100.7"]}
        kwargs = browser._build_cloakbrowser_launch_kwargs()

        self.assertEqual(1, sum(arg.startswith("--fingerprint-webrtc-ip") for arg in kwargs["args"]))

    def test_cloakbrowser_authenticated_http_proxy_uses_local_bridge(self):
        details = ProxyDetails("http", "proxy.example", 8080, "user", "pass")
        browser = self._make_cloakbrowser_shell(
            proxy_config={"server": "http://proxy.example:8080", "username": "user", "password": "pass"},
            proxy_details=details,
        )

        with patch.object(BrowserInterface, "_detect_browser_locale", return_value="en-US"), patch.object(
            BrowserInterface, "_detect_browser_timezone", return_value="UTC"
        ):
            kwargs = browser._build_cloakbrowser_launch_kwargs()

        proxy = kwargs["proxy"]
        self.assertIsInstance(proxy, dict)
        self.assertTrue(str(proxy.get("server", "")).startswith("http://127.0.0.1:"))
        self.assertNotIn("username", proxy)
        self.assertIsNotNone(browser._local_proxy)
        browser._local_proxy.stop()

    def test_cloakbrowser_authenticated_socks_proxy_uses_local_bridge(self):
        details = ProxyDetails("socks5", "proxy.example", 1080, "user", "pass")
        browser = self._make_cloakbrowser_shell(
            proxy_config={"server": "socks5://proxy.example:1080", "username": "user", "password": "pass"},
            proxy_details=details,
        )

        with patch.object(BrowserInterface, "_detect_browser_locale", return_value="en-US"), patch.object(
            BrowserInterface, "_detect_browser_timezone", return_value="UTC"
        ):
            kwargs = browser._build_cloakbrowser_launch_kwargs()

        proxy = kwargs["proxy"]
        self.assertIsInstance(proxy, dict)
        self.assertTrue(str(proxy.get("server", "")).startswith("socks5://127.0.0.1:"))
        self.assertNotIn("username", proxy)
        self.assertIsNotNone(browser._local_proxy)
        browser._local_proxy.stop()

    def test_parse_proxy_decodes_url_encoded_credentials(self):
        cfg, details = parse_proxy("http://user%40mail:p%40ss@1.2.3.4:8080")
        self.assertEqual(cfg["username"], "user@mail")
        self.assertEqual(cfg["password"], "p@ss")
        self.assertEqual(details.username, "user@mail")
        self.assertEqual(details.password, "p@ss")


if __name__ == "__main__":
    unittest.main()
