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

        elif url.startswith("file://"):
            # initialize empty lists for console messages
            captured_console = []

            # Process local file
            local_file_path = url[7:]  # Remove 'file://' prefix
            if not os.path.exists(local_file_path):
                raise FileNotFoundError(f"Local file not found: {local_file_path}")
            with open(local_file_path, "r", encoding="utf-8") as f:
                html = f.read()
            if config.screenshot:
                screenshot_data = await self._generate_screenshot_from_html(html)
            if config.capture_console_messages:
                page, context = await self.browser_manager.get_page(crawlerRunConfig=config)
                captured_console = await self._capture_console_messages(page, url)

            return AsyncCrawlResponse(
                html=html,
                response_headers=response_headers,
                status_code=status_code,
                screenshot=screenshot_data,
                get_delayed_content=None,
                console_messages=captured_console,
            )

        ##### 
        # Since both "raw:" and "raw://" start with "raw:", the first condition is always true for both, so "raw://" will be sliced as "//...", which is incorrect.
        # Fix: Check for "raw://" first, then "raw:"
        # Also, the prefix "raw://" is actually 6 characters long, not 7, so it should be sliced accordingly: url[6:]
        #####
        elif url.startswith("raw://") or url.startswith("raw:"):
            # Process raw HTML content
            # raw_html = url[4:] if url[:4] == "raw:" else url[7:]
            raw_html = url[6:] if url.startswith("raw://") else url[4:]
            html = raw_html
            if config.screenshot:
                screenshot_data = await self._generate_screenshot_from_html(html)
            return AsyncCrawlResponse(
                html=html,
                response_headers=response_headers,
                status_code=status_code,
                screenshot=screenshot_data,
                get_delayed_content=None,
            )
        else:
            raise ValueError(
                "URL must start with 'http://', 'https://', 'file://', or 'raw:'"
            )