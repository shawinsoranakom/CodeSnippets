async def _arun_stream(
        self,
        start_url: str,
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> AsyncGenerator[CrawlResult, None]:
        """
        Same traversal as :meth:`_arun_batch`, but yield pages immediately.

        Each popped URL is crawled, its metadata annotated, then the result gets
        yielded before we even look at the next stack entry. Successful crawls
        still feed :meth:`link_discovery`, keeping DFS order intact.
        """
        # Reset cancel event for strategy reuse
        self._cancel_event = asyncio.Event()

        # Conditional state initialization for resume support
        if self._resume_state:
            visited = set(self._resume_state.get("visited", []))
            stack = [
                (item["url"], item["parent_url"], item["depth"])
                for item in self._resume_state.get("stack", [])
            ]
            depths = dict(self._resume_state.get("depths", {}))
            self._pages_crawled = self._resume_state.get("pages_crawled", 0)
            self._dfs_seen = set(self._resume_state.get("dfs_seen", []))
        else:
            # Original initialization
            visited: Set[str] = set()
            stack: List[Tuple[str, Optional[str], int]] = [(start_url, None, 0)]
            depths: Dict[str, int] = {start_url: 0}
            self._reset_seen(start_url)

        while stack and not self._cancel_event.is_set():
            # Check external cancellation callback before processing this URL
            if await self._check_cancellation():
                self.logger.info("Crawl cancelled by user")
                break

            url, parent, depth = stack.pop()
            if url in visited or depth > self.max_depth:
                continue
            visited.add(url)

            stream_config = config.clone(deep_crawl_strategy=None, stream=True)
            stream_gen = await crawler.arun_many(urls=[url], config=stream_config)
            async for result in stream_gen:
                result.metadata = result.metadata or {}
                result.metadata["depth"] = depth
                result.metadata["parent_url"] = parent
                if self.url_scorer:
                    result.metadata["score"] = self.url_scorer.score(url)
                yield result

                # Only count successful crawls toward max_pages limit
                # and only discover links from successful crawls
                if result.success:
                    self._pages_crawled += 1
                    # Check if we've reached the limit during batch processing
                    if self._pages_crawled >= self.max_pages:
                        self.logger.info(f"Max pages limit ({self.max_pages}) reached during batch, stopping crawl")
                        break  # Exit the generator

                    new_links: List[Tuple[str, Optional[str]]] = []
                    await self.link_discovery(result, url, depth, visited, new_links, depths)
                    for new_url, new_parent in reversed(new_links):
                        new_depth = depths.get(new_url, depth + 1)
                        stack.append((new_url, new_parent, new_depth))

                    # Capture state after each URL processed (if callback set)
                    if self._on_state_change:
                        state = {
                            "strategy_type": "dfs",
                            "visited": list(visited),
                            "stack": [
                                {"url": u, "parent_url": p, "depth": d}
                                for u, p, d in stack
                            ],
                            "depths": depths,
                            "pages_crawled": self._pages_crawled,
                            "dfs_seen": list(self._dfs_seen),
                            "cancelled": self._cancel_event.is_set(),
                        }
                        self._last_state = state
                        await self._on_state_change(state)

        # Final state update if cancelled
        if self._cancel_event.is_set() and self._on_state_change:
            state = {
                "strategy_type": "dfs",
                "visited": list(visited),
                "stack": [
                    {"url": u, "parent_url": p, "depth": d}
                    for u, p, d in stack
                ],
                "depths": depths,
                "pages_crawled": self._pages_crawled,
                "dfs_seen": list(self._dfs_seen),
                "cancelled": True,
            }
            self._last_state = state
            await self._on_state_change(state)