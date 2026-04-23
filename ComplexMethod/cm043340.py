def _build_browser_args(self) -> dict:
        """Build browser launch arguments from config."""
        args = [
            "--disable-gpu",
            "--disable-gpu-compositing",
            "--disable-software-rasterizer",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-infobars",
            "--window-position=0,0",
            "--ignore-certificate-errors",
            "--ignore-certificate-errors-spki-list",
            "--disable-blink-features=AutomationControlled",
            "--window-position=400,0",
            "--disable-renderer-backgrounding",
            "--disable-ipc-flooding-protection",
            "--force-color-profile=srgb",
            "--mute-audio",
            "--disable-background-timer-throttling",
            # Memory-saving flags: disable unused Chrome features
            "--disable-features=OptimizationHints,MediaRouter,DialMediaRouteProvider",
            "--disable-component-update",
            "--disable-domain-reliability",
            # "--single-process",
            f"--window-size={self.config.viewport_width},{self.config.viewport_height}",
        ]

        if self.config.memory_saving_mode:
            args.extend([
                "--aggressive-cache-discard",
                '--js-flags=--max-old-space-size=512',
            ])

        if self.config.light_mode:
            args.extend(BROWSER_DISABLE_OPTIONS)

        if self.config.text_mode:
            args.extend(
                [
                    "--blink-settings=imagesEnabled=false",
                    "--disable-remote-fonts",
                    "--disable-images",
                    "--disable-javascript",
                    "--disable-software-rasterizer",
                    "--disable-dev-shm-usage",
                ]
            )

        if self.config.extra_args:
            args.extend(self.config.extra_args)

        # Deduplicate args
        args = list(dict.fromkeys(args))

        browser_args = {"headless": self.config.headless, "args": args}

        if self.config.chrome_channel:
            browser_args["channel"] = self.config.chrome_channel

        if self.config.accept_downloads:
            browser_args["downloads_path"] = self.config.downloads_path or os.path.join(
                os.getcwd(), "downloads"
            )
            os.makedirs(browser_args["downloads_path"], exist_ok=True)

        if self.config.proxy:
            warnings.warn(
                "BrowserConfig.proxy is deprecated and ignored. Use proxy_config instead.",
                DeprecationWarning,
            )
        if self.config.proxy_config:
            from playwright.async_api import ProxySettings

            proxy_settings = ProxySettings(
                server=self.config.proxy_config.server,
                username=self.config.proxy_config.username,
                password=self.config.proxy_config.password,
            )
            browser_args["proxy"] = proxy_settings

        return browser_args