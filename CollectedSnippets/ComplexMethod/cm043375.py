async def _arun_best_first(
        self,
        start_url: str,
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> AsyncGenerator[CrawlResult, None]:
        """
        Core best-first crawl method using a priority queue.

        The queue items are tuples of (score, depth, url, parent_url). Lower scores
        are treated as higher priority. URLs are processed in batches for efficiency.
        """
        # Reset cancel event for strategy reuse
        self._cancel_event = asyncio.Event()

        queue: asyncio.PriorityQueue = asyncio.PriorityQueue()

        # Conditional state initialization for resume support
        if self._resume_state:
            visited = set(self._resume_state.get("visited", []))
            depths = dict(self._resume_state.get("depths", {}))
            self._pages_crawled = self._resume_state.get("pages_crawled", 0)
            # Restore queue from saved items
            queue_items = self._resume_state.get("queue_items", [])
            for item in queue_items:
                await queue.put((item["score"], item["depth"], item["url"], item["parent_url"]))
            # Initialize shadow list if callback is set
            if self._on_state_change:
                self._queue_shadow = [
                    (item["score"], item["depth"], item["url"], item["parent_url"])
                    for item in queue_items
                ]
        else:
            # Original initialization
            initial_score = self.url_scorer.score(start_url) if self.url_scorer else 0
            await queue.put((-initial_score, 0, start_url, None))
            visited: Set[str] = set()
            depths: Dict[str, int] = {start_url: 0}
            # Initialize shadow list if callback is set
            if self._on_state_change:
                self._queue_shadow = [(-initial_score, 0, start_url, None)]

        while not queue.empty() and not self._cancel_event.is_set():
            # Stop if we've reached the max pages limit
            if self._pages_crawled >= self.max_pages:
                self.logger.info(f"Max pages limit ({self.max_pages}) reached, stopping crawl")
                break

            # Check external cancellation callback before processing this batch
            if await self._check_cancellation():
                self.logger.info("Crawl cancelled by user")
                break

            # Calculate how many more URLs we can process in this batch
            remaining = self.max_pages - self._pages_crawled
            batch_size = min(BATCH_SIZE, remaining)
            if batch_size <= 0:
                # No more pages to crawl
                self.logger.info(f"Max pages limit ({self.max_pages}) reached, stopping crawl")
                break

            batch: List[Tuple[float, int, str, Optional[str]]] = []
            # Retrieve up to BATCH_SIZE items from the priority queue.
            for _ in range(BATCH_SIZE):
                if queue.empty():
                    break
                item = await queue.get()
                # Remove from shadow list if tracking
                if self._on_state_change and self._queue_shadow is not None:
                    try:
                        self._queue_shadow.remove(item)
                    except ValueError:
                        pass  # Item may have been removed already
                score, depth, url, parent_url = item
                if url in visited:
                    continue
                visited.add(url)
                batch.append(item)

            if not batch:
                continue

            # Process the current batch of URLs.
            urls = [item[2] for item in batch]
            batch_config = config.clone(deep_crawl_strategy=None, stream=True)
            stream_gen = await crawler.arun_many(urls=urls, config=batch_config)
            async for result in stream_gen:
                result_url = result.url
                # Find the corresponding tuple from the batch.
                corresponding = next((item for item in batch if item[2] == result_url), None)
                if not corresponding:
                    continue
                score, depth, url, parent_url = corresponding
                result.metadata = result.metadata or {}
                result.metadata["depth"] = depth
                result.metadata["parent_url"] = parent_url
                result.metadata["score"] = -score

                # Count only successful crawls toward max_pages limit
                if result.success:
                    self._pages_crawled += 1
                    # Check if we've reached the limit during batch processing
                    if self._pages_crawled >= self.max_pages:
                        self.logger.info(f"Max pages limit ({self.max_pages}) reached during batch, stopping crawl")
                        break  # Exit the generator

                yield result

                # Only discover links from successful crawls
                if result.success:
                    # Discover new links from this result
                    new_links: List[Tuple[str, Optional[str]]] = []
                    await self.link_discovery(result, result_url, depth, visited, new_links, depths)

                    for new_url, new_parent in new_links:
                        new_depth = depths.get(new_url, depth + 1)
                        new_score = self.url_scorer.score(new_url) if self.url_scorer else 0
                        # Skip URLs with scores below the threshold
                        if new_score < self.score_threshold:
                            self.logger.debug(
                                f"URL {new_url} skipped: score {new_score} below threshold {self.score_threshold}"
                            )
                            self.stats.urls_skipped += 1
                            continue
                        queue_item = (-new_score, new_depth, new_url, new_parent)
                        await queue.put(queue_item)
                        # Add to shadow list if tracking
                        if self._on_state_change and self._queue_shadow is not None:
                            self._queue_shadow.append(queue_item)

                    # Capture state after EACH URL processed (if callback set)
                    if self._on_state_change and self._queue_shadow is not None:
                        state = {
                            "strategy_type": "best_first",
                            "visited": list(visited),
                            "queue_items": [
                                {"score": s, "depth": d, "url": u, "parent_url": p}
                                for s, d, u, p in self._queue_shadow
                            ],
                            "depths": depths,
                            "pages_crawled": self._pages_crawled,
                            "cancelled": self._cancel_event.is_set(),
                        }
                        self._last_state = state
                        await self._on_state_change(state)

        # Final state update if cancelled
        if self._cancel_event.is_set() and self._on_state_change and self._queue_shadow is not None:
            state = {
                "strategy_type": "best_first",
                "visited": list(visited),
                "queue_items": [
                    {"score": s, "depth": d, "url": u, "parent_url": p}
                    for s, d, u, p in self._queue_shadow
                ],
                "depths": depths,
                "pages_crawled": self._pages_crawled,
                "cancelled": True,
            }
            self._last_state = state
            await self._on_state_change(state)