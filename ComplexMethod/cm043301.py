async def extract_head_for_urls(
        self,
        urls: List[str],
        config: Optional["SeedingConfig"] = None,
        concurrency: int = 10,
        timeout: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Extract head content for a custom list of URLs using URLSeeder's parallel processing.

        This method reuses URLSeeder's efficient parallel processing, caching, and head extraction
        logic to process a custom list of URLs rather than discovering URLs from sources.

        Parameters
        ----------
        urls : List[str]
            List of URLs to extract head content from
        config : SeedingConfig, optional
            Configuration object. If None, uses default settings for head extraction
        concurrency : int, default=10
            Number of concurrent requests
        timeout : int, default=5
            Timeout for each request in seconds

        Returns
        -------
        List[Dict[str, Any]]
            List of dictionaries containing url, status, head_data, and optional relevance_score
        """
        # Create default config if none provided
        if config is None:
            # Import here to avoid circular imports
            from .async_configs import SeedingConfig
            config = SeedingConfig(
                extract_head=True,
                concurrency=concurrency,
                verbose=False
            )

        # Override concurrency and ensure head extraction is enabled
        config.concurrency = concurrency
        config.extract_head = True

        self._log("info", "Starting head extraction for {count} custom URLs",
                  params={"count": len(urls)}, tag="URL_SEED")

        # Setup rate limiting if specified in config
        if config.hits_per_sec:
            if config.hits_per_sec <= 0:
                self._log("warning", "hits_per_sec must be positive. Disabling rate limiting.", tag="URL_SEED")
                self._rate_sem = None
            else:
                self._rate_sem = asyncio.Semaphore(config.hits_per_sec)
        else:
            self._rate_sem = None

        # Use bounded queue to prevent memory issues with large URL lists
        queue_size = min(10000, max(1000, concurrency * 100))
        queue = asyncio.Queue(maxsize=queue_size)
        producer_done = asyncio.Event()
        stop_event = asyncio.Event()
        seen: set[str] = set()

        # Results collection
        results: List[Dict[str, Any]] = []

        async def producer():
            """Producer to feed URLs into the queue."""
            try:
                for url in urls:
                    if url in seen:
                        self._log("debug", "Skipping duplicate URL: {url}",
                                  params={"url": url}, tag="URL_SEED")
                        continue
                    if stop_event.is_set():
                        break
                    seen.add(url)
                    await queue.put(url)
            finally:
                producer_done.set()

        async def worker(res_list: List[Dict[str, Any]]):
            """Worker to process URLs from the queue."""
            while True:
                try:
                    # Wait for URL or producer completion
                    url = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    if producer_done.is_set() and queue.empty():
                        break
                    continue

                try:
                    # Use existing _validate method which handles head extraction, caching, etc.
                    await self._validate(
                        url, res_list, 
                        live=False,  # We're not doing live checks, just head extraction
                        extract=True,  # Always extract head content
                        timeout=timeout,
                        verbose=config.verbose or False,
                        query=config.query,
                        score_threshold=config.score_threshold,
                        scoring_method=config.scoring_method or "bm25",
                        filter_nonsense=config.filter_nonsense_urls
                    )
                except Exception as e:
                    self._log("error", "Failed to process URL {url}: {error}",
                              params={"url": url, "error": str(e)}, tag="URL_SEED")
                    # Add failed entry to results
                    res_list.append({
                        "url": url,
                        "status": "failed",
                        "head_data": {},
                        "error": str(e)
                    })
                finally:
                    queue.task_done()

        # Start producer
        producer_task = asyncio.create_task(producer())

        # Start workers
        worker_tasks = []
        for _ in range(concurrency):
            worker_task = asyncio.create_task(worker(results))
            worker_tasks.append(worker_task)

        # Wait for producer to finish
        await producer_task

        # Wait for all items to be processed
        await queue.join()

        # Cancel workers
        for task in worker_tasks:
            task.cancel()

        # Wait for workers to finish canceling
        await asyncio.gather(*worker_tasks, return_exceptions=True)

        # Apply BM25 scoring if query is provided
        if config.query and config.scoring_method == "bm25":
            results = await self._apply_bm25_scoring(results, config)

        # Apply score threshold filtering
        if config.score_threshold is not None:
            results = [r for r in results if r.get("relevance_score", 0) >= config.score_threshold]

        # Sort by relevance score if available
        if any("relevance_score" in r for r in results):
            results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        self._log("info", "Completed head extraction for {count} URLs, {success} successful",
                  params={
                      "count": len(urls),
                      "success": len([r for r in results if r.get("status") == "valid"])
                  }, tag="URL_SEED")

        return results