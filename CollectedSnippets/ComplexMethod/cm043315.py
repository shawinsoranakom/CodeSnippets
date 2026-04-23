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