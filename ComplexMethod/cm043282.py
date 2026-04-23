async def crawl(
        self, url: str, config: CrawlerRunConfig, **kwargs
    ) -> AsyncCrawlResponse:
        """
        Crawls a given URL or processes raw HTML/local file content based on the URL prefix.

        Args:
            url (str): The URL to crawl. Supported prefixes:
                - 'http://' or 'https://': Web URL to crawl.
                - 'file://': Local file path to process.
                - 'raw://': Raw HTML content to process.
            **kwargs: Additional parameters:
                - 'screenshot' (bool): Whether to take a screenshot.
                - ... [other existing parameters]

        Returns:
            AsyncCrawlResponse: The response containing HTML, headers, status code, and optional screenshot.
        """
        config = config or CrawlerRunConfig.from_kwargs(kwargs)
        response_headers = {}
        status_code = 200  # Default for local/raw HTML
        screenshot_data = None

        if url.startswith(("http://", "https://", "view-source:")):
            return await self._crawl_web(url, config)

        elif url.startswith("file://") or url.startswith("raw://") or url.startswith("raw:"):
            # Check if browser processing is required for file:// or raw: URLs
            needs_browser = (
                config.process_in_browser or
                config.screenshot or
                config.pdf or
                config.capture_mhtml or
                config.js_code or
                config.wait_for or
                config.scan_full_page or
                config.remove_overlay_elements or
                config.remove_consent_popups or
                config.simulate_user or
                config.magic or
                config.process_iframes or
                config.capture_console_messages or
                config.capture_network_requests
            )

            if needs_browser:
                # Route through _crawl_web() for full browser pipeline
                # _crawl_web() will detect file:// and raw: URLs and use set_content()
                return await self._crawl_web(url, config)

            # Fast path: return HTML directly without browser interaction
            if url.startswith("file://"):
                # Process local file
                local_file_path = url[7:]  # Remove 'file://' prefix
                if not os.path.exists(local_file_path):
                    raise FileNotFoundError(f"Local file not found: {local_file_path}")
                with open(local_file_path, "r", encoding="utf-8") as f:
                    html = f.read()
            else:
                # Process raw HTML content (raw:// or raw:)
                html = url[6:] if url.startswith("raw://") else url[4:]

            return AsyncCrawlResponse(
                html=html,
                response_headers=response_headers,
                status_code=status_code,
                screenshot=None,
                pdf_data=None,
                mhtml_data=None,
                get_delayed_content=None,
                # For raw:/file:// URLs, use base_url if provided; don't fall back to the raw content
                redirected_url=config.base_url,
            )
        else:
            raise ValueError(
                "URL must start with 'http://', 'https://', 'file://', or 'raw:'"
            )