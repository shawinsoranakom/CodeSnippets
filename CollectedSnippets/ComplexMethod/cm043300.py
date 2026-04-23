async def urls(self,
                   domain: str,
                   config: "SeedingConfig",
                   ) -> List[Dict[str, Any]]:
        """
        Fetch URLs for a domain using configuration from SeedingConfig.

        Parameters
        ----------
        domain : str
            The domain to fetch URLs for (e.g., "example.com")
        config : SeedingConfig
            Configuration object containing all seeding parameters
        """
        # Extract parameters from config
        pattern = config.pattern or "*"
        source = config.source
        live_check = config.live_check
        extract_head = config.extract_head
        concurrency = config.concurrency
        head_timeout = 5  # Default timeout for HEAD requests
        hits_per_sec = config.hits_per_sec
        self.force = config.force  # Store force flag as instance attribute
        force = config.force
        verbose = config.verbose if config.verbose is not None else (
            self.logger.verbose if self.logger else False)
        max_urls = config.max_urls if config.max_urls is not None else -1
        query = config.query
        score_threshold = config.score_threshold
        scoring_method = config.scoring_method

        # Store cache config for use in _from_sitemaps
        self._cache_ttl_hours = getattr(config, 'cache_ttl_hours', 24)
        self._validate_sitemap_lastmod = getattr(config, 'validate_sitemap_lastmod', True)

        # Ensure seeder's logger verbose matches the config's verbose if it's set
        if self.logger and hasattr(self.logger, 'verbose') and config.verbose is not None:
            self.logger.verbose = config.verbose

        # Parse source parameter - split by '+' to get list of sources
        sources = [s.strip().lower() for s in source.split("+") if s.strip()]

        valid_sources = {"cc", "sitemap"}
        for s in sources:
            if s not in valid_sources:
                raise ValueError(
                    f"Invalid source '{s}'. Valid sources are: {', '.join(valid_sources)}")

            # ensure we have the latest CC collection id when the source is cc
            if s == "cc" and self.index_id is None:
                self.index_id = await self._latest_index()


        if hits_per_sec:
            if hits_per_sec <= 0:
                self._log(
                    "warning", "hits_per_sec must be positive. Disabling rate limiting.", tag="URL_SEED")
                self._rate_sem = None
            else:
                self._rate_sem = asyncio.Semaphore(hits_per_sec)
        else:
            self._rate_sem = None  # Ensure it's None if no rate limiting

        self._log("info", "Starting URL seeding for {domain} with source={source}",
                  params={"domain": domain, "source": source}, tag="URL_SEED")

        # choose stream
        async def gen():
            if "sitemap" in sources:
                self._log("debug", "Fetching from sitemaps...", tag="URL_SEED")
                async for u in self._from_sitemaps(domain, pattern, force):
                    yield u
            if "cc" in sources:
                self._log("debug", "Fetching from Common Crawl...",
                          tag="URL_SEED")
                async for u in self._from_cc(domain, pattern, force):
                    yield u

        # Use bounded queue to prevent RAM spikes with large domains
        queue_size = min(10000, max(1000, concurrency * 100))  # Dynamic size based on concurrency
        queue = asyncio.Queue(maxsize=queue_size)
        producer_done = asyncio.Event()
        stop_event = asyncio.Event()
        seen: set[str] = set()
        filter_nonsense = config.filter_nonsense_urls  # Extract this for passing to workers

        async def producer():
            try:
                async for u in gen():
                    try:
                        if u in seen:
                            self._log("debug", "Skipping duplicate URL: {url}",
                                      params={"url": u}, tag="URL_SEED")
                            continue
                        if stop_event.is_set():
                            self._log(
                                "info", "Producer stopping due to max_urls limit.", tag="URL_SEED")
                            break
                        seen.add(u)
                        await queue.put(u)  # Will block if queue is full, providing backpressure
                    except UnicodeEncodeError:
                        # Skip URLs that cause encoding errors (e.g. on Windows)
                        continue
            except Exception as e:
                self._log("error", "Producer encountered an error: {error}", params={
                          "error": str(e)}, tag="URL_SEED")
            finally:
                producer_done.set()
                self._log("debug", "Producer finished.", tag="URL_SEED")

        async def worker(res_list: List[Dict[str, Any]]):
            while True:
                if queue.empty() and producer_done.is_set():
                    # self._log("debug", "Worker exiting: queue empty and producer done.", tag="URL_SEED")
                    break
                try:
                    # Increased timeout slightly
                    url = await asyncio.wait_for(queue.get(), 5)
                except asyncio.TimeoutError:
                    continue  # Keep checking queue and producer_done status
                except Exception as e:
                    self._log("error", "Worker failed to get URL from queue: {error}", params={
                              "error": str(e)}, tag="URL_SEED")
                    continue

                if max_urls > 0 and len(res_list) >= max_urls:
                    self._log(
                        "info",
                        "Worker stopping due to max_urls limit.",
                        tag="URL_SEED",
                    )
                    stop_event.set()

                    # mark the current item done
                    queue.task_done()

                    # flush whatever is still sitting in the queue so
                    # queue.join() can finish cleanly
                    while not queue.empty():
                        try:
                            queue.get_nowait()
                            queue.task_done()
                        except asyncio.QueueEmpty:
                            break
                    break

                if self._rate_sem:  # global QPS control
                    async with self._rate_sem:
                        await self._validate(url, res_list, live_check, extract_head,
                                             head_timeout, verbose, query, score_threshold, scoring_method,
                                             filter_nonsense)
                else:
                    await self._validate(url, res_list, live_check, extract_head,
                                         head_timeout, verbose, query, score_threshold, scoring_method,
                                         filter_nonsense)
                queue.task_done()  # Mark task as done for queue.join() if ever used

        # launch
        results: List[Dict[str, Any]] = []
        prod_task = asyncio.create_task(producer())
        workers = [asyncio.create_task(worker(results))
                   for _ in range(concurrency)]

        # Wait for all workers to finish
        await asyncio.gather(prod_task, *workers)
        await queue.join()  # Ensure all queued items are processed

        self._log("info", "Finished URL seeding for {domain}. Total URLs: {count}",
                  params={"domain": domain, "count": len(results)}, tag="URL_SEED")

        # Apply BM25 scoring if query was provided
        if query and extract_head and scoring_method == "bm25":
            # Apply collective BM25 scoring across all documents
            results = await self._apply_bm25_scoring(results, config)

            # Filter by score threshold if specified
            if score_threshold is not None:
                original_count = len(results)
                results = [r for r in results if r.get("relevance_score", 0) >= score_threshold]
                if original_count > len(results):
                    self._log("info", "Filtered {filtered} URLs below score threshold {threshold}",
                              params={"filtered": original_count - len(results), "threshold": score_threshold}, tag="URL_SEED")

            # Sort by relevance score
            results.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
            self._log("info", "Sorted {count} URLs by relevance score for query: '{query}'",
                      params={"count": len(results), "query": query}, tag="URL_SEED")
        elif query and not extract_head:
            self._log(
                "warning", "Query provided but extract_head is False. Enable extract_head for relevance scoring.", tag="URL_SEED")

        return results[:max_urls] if max_urls > 0 else results