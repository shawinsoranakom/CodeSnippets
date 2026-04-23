async def _arun_stream(
        self,
        start_url: str,
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> AsyncGenerator[CrawlResult, None]:
        """
        Streaming mode:
        Processes one BFS level at a time and yields results immediately as they arrive.
        """
        # Reset cancel event for strategy reuse
        self._cancel_event = asyncio.Event()

        # Conditional state initialization for resume support
        if self._resume_state:
            visited = set(self._resume_state.get("visited", []))
            current_level = [
                (item["url"], item["parent_url"])
                for item in self._resume_state.get("pending", [])
            ]
            depths = dict(self._resume_state.get("depths", {}))
            self._pages_crawled = self._resume_state.get("pages_crawled", 0)
        else:
            # Original initialization
            visited: Set[str] = set()
            current_level: List[Tuple[str, Optional[str]]] = [(start_url, None)]
            depths: Dict[str, int] = {start_url: 0}

        while current_level and not self._cancel_event.is_set():
            # Check external cancellation callback before processing this level
            if await self._check_cancellation():
                self.logger.info("Crawl cancelled by user")
                break

            next_level: List[Tuple[str, Optional[str]]] = []
            urls = [url for url, _ in current_level]
            visited.update(urls)

            stream_config = config.clone(deep_crawl_strategy=None, stream=True)
            stream_gen = await crawler.arun_many(urls=urls, config=stream_config)

            # Keep track of processed results for this batch
            results_count = 0
            async for result in stream_gen:
                url = result.url
                depth = depths.get(url, 0)
                result.metadata = result.metadata or {}
                result.metadata["depth"] = depth
                parent_url = next((parent for (u, parent) in current_level if u == url), None)
                result.metadata["parent_url"] = parent_url

                # Count only successful crawls
                if result.success:
                    self._pages_crawled += 1
                    # Check if we've reached the limit during batch processing
                    if self._pages_crawled >= self.max_pages:
                        self.logger.info(f"Max pages limit ({self.max_pages}) reached during batch, stopping crawl")
                        break  # Exit the generator

                results_count += 1
                yield result

                # Only discover links from successful crawls
                if result.success:
                    # Link discovery will handle the max pages limit internally
                    await self.link_discovery(result, url, depth, visited, next_level, depths)

                    # Capture state after EACH URL processed (if callback set)
                    if self._on_state_change:
                        state = {
                            "strategy_type": "bfs",
                            "visited": list(visited),
                            "pending": [{"url": u, "parent_url": p} for u, p in next_level],
                            "depths": depths,
                            "pages_crawled": self._pages_crawled,
                            "cancelled": self._cancel_event.is_set(),
                        }
                        self._last_state = state
                        await self._on_state_change(state)

            # If we didn't get results back (e.g. due to errors), avoid getting stuck in an infinite loop
            # by considering these URLs as visited but not counting them toward the max_pages limit
            if results_count == 0 and urls:
                self.logger.warning(f"No results returned for {len(urls)} URLs, marking as visited")

            current_level = next_level

        # Final state update if cancelled
        if self._cancel_event.is_set() and self._on_state_change:
            state = {
                "strategy_type": "bfs",
                "visited": list(visited),
                "pending": [{"url": u, "parent_url": p} for u, p in current_level],
                "depths": depths,
                "pages_crawled": self._pages_crawled,
                "cancelled": True,
            }
            self._last_state = state
            await self._on_state_change(state)