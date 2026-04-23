async def _arun_batch(
        self,
        start_url: str,
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> List[CrawlResult]:
        """
        Batch (non-streaming) mode:
        Processes one BFS level at a time, then yields all the results.
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
            # current_level holds tuples: (url, parent_url)
            current_level: List[Tuple[str, Optional[str]]] = [(start_url, None)]
            depths: Dict[str, int] = {start_url: 0}

        results: List[CrawlResult] = []

        while current_level and not self._cancel_event.is_set():
            # Check if we've already reached max_pages before starting a new level
            if self._pages_crawled >= self.max_pages:
                self.logger.info(f"Max pages limit ({self.max_pages}) reached, stopping crawl")
                break

            # Check external cancellation callback before processing this level
            if await self._check_cancellation():
                self.logger.info("Crawl cancelled by user")
                break

            next_level: List[Tuple[str, Optional[str]]] = []
            urls = [url for url, _ in current_level]

            # Clone the config to disable deep crawling recursion and enforce batch mode.
            batch_config = config.clone(deep_crawl_strategy=None, stream=False)
            batch_results = await crawler.arun_many(urls=urls, config=batch_config)

            for result in batch_results:
                url = result.url
                depth = depths.get(url, 0)
                result.metadata = result.metadata or {}
                result.metadata["depth"] = depth
                parent_url = next((parent for (u, parent) in current_level if u == url), None)
                result.metadata["parent_url"] = parent_url
                results.append(result)

                # Only discover links from successful crawls
                if result.success:
                    # Increment pages crawled per URL for accurate state tracking
                    self._pages_crawled += 1

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

        return results