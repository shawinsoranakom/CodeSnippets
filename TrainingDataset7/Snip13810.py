def set_emulated_media(self, *, media=None, features=None):
        if self.browser not in {"chrome", "edge"}:
            self.skipTest(
                "Emulation.setEmulatedMedia is only supported on Chromium and "
                "Chrome-based browsers. See https://chromedevtools.github.io/devtools-"
                "protocol/1-3/Emulation/#method-setEmulatedMedia for more details."
            )
        params = {}
        if media is not None:
            params["media"] = media
        if features is not None:
            params["features"] = features

        # Not using .execute_cdp_cmd() as it isn't supported by the remote web
        # driver when using --selenium-hub.
        self.selenium.execute(
            driver_command="executeCdpCommand",
            params={"cmd": "Emulation.setEmulatedMedia", "params": params},
        )