async def setup_context(
        self,
        context: BrowserContext,
        crawlerRunConfig: CrawlerRunConfig = None,
        is_default=False,
    ):
        """
        Set up a browser context with the configured options.

        How it works:
        1. Set extra HTTP headers if provided.
        2. Add cookies if provided.
        3. Load storage state if provided.
        4. Accept downloads if enabled.
        5. Set default timeouts for navigation and download.
        6. Set user agent if provided.
        7. Set browser hints if provided.
        8. Set proxy if provided.
        9. Set downloads path if provided.
        10. Set storage state if provided.
        11. Set cache if provided.
        12. Set extra HTTP headers if provided.
        13. Add cookies if provided.
        14. Set default timeouts for navigation and download if enabled.
        15. Set user agent if provided.
        16. Set browser hints if provided.

        Args:
            context (BrowserContext): The browser context to set up
            crawlerRunConfig (CrawlerRunConfig): Configuration object containing all browser settings
            is_default (bool): Flag indicating if this is the default context
        Returns:
            None
        """
        if self.config.headers:
            await context.set_extra_http_headers(self.config.headers)

        if self.config.cookies:
            await context.add_cookies(self.config.cookies)

        if self.config.storage_state:
            await context.storage_state(path=None)

        if self.config.accept_downloads:
            context.set_default_timeout(DOWNLOAD_PAGE_TIMEOUT)
            context.set_default_navigation_timeout(DOWNLOAD_PAGE_TIMEOUT)
            if self.config.downloads_path:
                context._impl_obj._options["accept_downloads"] = True
                context._impl_obj._options[
                    "downloads_path"
                ] = self.config.downloads_path

        # Handle user agent and browser hints
        if self.config.user_agent:
            combined_headers = {
                "User-Agent": self.config.user_agent,
                "sec-ch-ua": self.config.browser_hint,
            }
            combined_headers.update(self.config.headers)
            await context.set_extra_http_headers(combined_headers)

        # Add default cookie (skip for raw:/file:// URLs which are not valid cookie URLs)
        cookie_url = None
        if crawlerRunConfig and crawlerRunConfig.url:
            url = crawlerRunConfig.url
            # Only set cookie for http/https URLs
            if url.startswith(("http://", "https://")):
                cookie_url = url
            elif crawlerRunConfig.base_url and crawlerRunConfig.base_url.startswith(("http://", "https://")):
                # Use base_url as fallback for raw:/file:// URLs
                cookie_url = crawlerRunConfig.base_url

        if cookie_url:
            await context.add_cookies(
                [
                    {
                        "name": "cookiesEnabled",
                        "value": "true",
                        "url": cookie_url,
                    }
                ]
            )

        # Handle navigator overrides
        if crawlerRunConfig:
            if (
                crawlerRunConfig.override_navigator
                or crawlerRunConfig.simulate_user
                or crawlerRunConfig.magic
            ):
                await context.add_init_script(load_js_script("navigator_overrider"))
                context._crawl4ai_nav_overrider_injected = True

        # Force-open closed shadow roots when flatten_shadow_dom is enabled
        if crawlerRunConfig and crawlerRunConfig.flatten_shadow_dom:
            await context.add_init_script("""
                const _origAttachShadow = Element.prototype.attachShadow;
                Element.prototype.attachShadow = function(init) {
                    return _origAttachShadow.call(this, {...init, mode: 'open'});
                };
            """)
            context._crawl4ai_shadow_dom_injected = True

        # Apply custom init_scripts from BrowserConfig (for stealth evasions, etc.)
        if self.config.init_scripts:
            for script in self.config.init_scripts:
                await context.add_init_script(script)