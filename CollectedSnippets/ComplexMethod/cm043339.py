async def start(self):
        """
        Start the browser instance and set up the default context.

        How it works:
        1. Check if Playwright is already initialized.
        2. If not, initialize Playwright.
        3. If managed browser is used, start it and connect to the CDP endpoint.
        4. If managed browser is not used, launch the browser and set up the default context.

        Note: This method should be called in a separate task to avoid blocking the main event loop.
        """
        if self.playwright is not None:
            await self.close()

        # Use cached CDP connection if enabled and cdp_url is set
        if self.config.cache_cdp_connection and self.config.cdp_url:
            self._using_cached_cdp = True
            self.config.use_managed_browser = True
            self.playwright, self.browser = await _CDPConnectionCache.acquire(
                self.config.cdp_url, self.use_undetected
            )
        else:
            self._using_cached_cdp = False
            if self.use_undetected:
                from patchright.async_api import async_playwright
            else:
                from playwright.async_api import async_playwright

            # Initialize playwright
            self.playwright = await async_playwright().start()

        # ── Persistent context via Playwright's native API ──────────────
        # When use_persistent_context is set and we're not connecting to an
        # external CDP endpoint, use launch_persistent_context() instead of
        # subprocess + CDP.  This properly supports proxy authentication
        # (server + username + password) which the --proxy-server CLI flag
        # cannot handle.
        if (
            self.config.use_persistent_context
            and not self.config.cdp_url
            and not self._using_cached_cdp
        ):
            # Collect stealth / optimization CLI flags, excluding ones that
            # launch_persistent_context handles via keyword arguments.
            _skip_prefixes = (
                "--proxy-server",
                "--remote-debugging-port",
                "--user-data-dir",
                "--headless",
                "--window-size",
            )
            cli_args = [
                flag
                for flag in ManagedBrowser.build_browser_flags(self.config)
                if not flag.startswith(_skip_prefixes)
            ]
            if self.config.extra_args:
                cli_args.extend(self.config.extra_args)

            launch_kwargs = {
                "headless": self.config.headless,
                "args": list(dict.fromkeys(cli_args)),  # dedupe
                "viewport": {
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height,
                },
                "user_agent": self.config.user_agent or None,
                "ignore_https_errors": self.config.ignore_https_errors,
                "accept_downloads": self.config.accept_downloads,
            }

            if self.config.proxy_config:
                launch_kwargs["proxy"] = {
                    "server": self.config.proxy_config.server,
                    "username": self.config.proxy_config.username,
                    "password": self.config.proxy_config.password,
                }

            if self.config.storage_state:
                launch_kwargs["storage_state"] = self.config.storage_state

            user_data_dir = self.config.user_data_dir or tempfile.mkdtemp(
                prefix="crawl4ai-persistent-"
            )

            self.default_context = (
                await self.playwright.chromium.launch_persistent_context(
                    user_data_dir, **launch_kwargs
                )
            )
            self.browser = None  # persistent context has no separate Browser
            self._launched_persistent = True

            await self.setup_context(self.default_context)

            # Set the browser endpoint key for global page tracking
            self._browser_endpoint_key = self._compute_browser_endpoint_key()
            if self._browser_endpoint_key not in BrowserManager._global_pages_in_use:
                BrowserManager._global_pages_in_use[self._browser_endpoint_key] = set()
            return

        if self.config.cdp_url or self.config.use_managed_browser:
            self.config.use_managed_browser = True

            if not self._using_cached_cdp:
                cdp_url = await self.managed_browser.start() if not self.config.cdp_url else self.config.cdp_url

                # Add CDP endpoint verification before connecting
                if not await self._verify_cdp_ready(cdp_url):
                    raise Exception(f"CDP endpoint at {cdp_url} is not ready after startup")

                self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)

            contexts = self.browser.contexts

            # If browser_context_id is provided, we're using a pre-created context
            if self.config.browser_context_id:
                if self.logger:
                    self.logger.debug(
                        f"Using pre-existing browser context: {self.config.browser_context_id}",
                        tag="BROWSER"
                    )
                # When connecting to a pre-created context, it should be in contexts
                if contexts:
                    self.default_context = contexts[0]
                    if self.logger:
                        self.logger.debug(
                            f"Found {len(contexts)} existing context(s), using first one",
                            tag="BROWSER"
                        )
                else:
                    # Context was created but not yet visible - wait a bit
                    await asyncio.sleep(0.2)
                    contexts = self.browser.contexts
                    if contexts:
                        self.default_context = contexts[0]
                    else:
                        # Still no contexts - this shouldn't happen with pre-created context
                        if self.logger:
                            self.logger.warning(
                                "Pre-created context not found, creating new one",
                                tag="BROWSER"
                            )
                        self.default_context = await self.create_browser_context()
            elif contexts:
                self.default_context = contexts[0]
            else:
                self.default_context = await self.create_browser_context()
            await self.setup_context(self.default_context)
        else:
            browser_args = self._build_browser_args()

            # Launch appropriate browser type
            if self.config.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(**browser_args)
            elif self.config.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(**browser_args)
            else:
                self.browser = await self.playwright.chromium.launch(**browser_args)

            self.default_context = self.browser

        # Set the browser endpoint key for global page tracking
        self._browser_endpoint_key = self._compute_browser_endpoint_key()
        # Initialize global tracking set for this endpoint if needed
        if self._browser_endpoint_key not in BrowserManager._global_pages_in_use:
            BrowserManager._global_pages_in_use[self._browser_endpoint_key] = set()