import unittest
from pathlib import Path

from app.core.browser_interface import BrowserInterface
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

    def test_cloakbrowser_proxy_adds_webrtc_auto_arg_once(self):
        browser = BrowserInterface.__new__(BrowserInterface)
        browser.profile_root = Path("tmp")
        browser._browser_settings = {}
        browser._cloakbrowser_defaults = dict(
            CLOAKBROWSER_DEFAULTS,
            locale="en-US",
            timezone="UTC",
            fingerprint_seed=12345,
        )
        browser._proxy_config = {"server": "http://proxy.example:8080"}

        kwargs = browser._build_cloakbrowser_launch_kwargs()

        self.assertIn("--fingerprint-webrtc-ip=auto", kwargs["args"])

        browser._browser_settings = {"launch_args": ["--fingerprint-webrtc-ip=198.51.100.7"]}
        kwargs = browser._build_cloakbrowser_launch_kwargs()

        self.assertEqual(1, sum(arg.startswith("--fingerprint-webrtc-ip") for arg in kwargs["args"]))


if __name__ == "__main__":
    unittest.main()
