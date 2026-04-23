def _search_ddgs(self, query: str, num_results: int) -> list[SearchResult]:
        """
        Search using DDGS multi-engine search.

        Tries multiple backends in order until one succeeds:
        DuckDuckGo -> Bing -> Brave -> Google -> Mojeek -> Yahoo -> Yandex
        """
        if not query:
            return []

        # Determine which backends to try
        if self.config.ddgs_backend == "auto":
            backends_to_try = DDGS_BACKENDS.copy()
        else:
            # Put configured backend first, then others as fallback
            backends_to_try = [self.config.ddgs_backend] + [
                b for b in DDGS_BACKENDS if b != self.config.ddgs_backend
            ]

        max_attempts = min(self.config.duckduckgo_max_attempts, len(backends_to_try))
        last_error: Optional[Exception] = None

        for backend in backends_to_try[:max_attempts]:
            try:
                logger.debug(f"Trying DDGS backend: {backend}")
                raw_results = self.ddgs_client.text(
                    query,
                    max_results=num_results,
                    backend=backend,
                    region=self.config.ddgs_region,
                    safesearch=self.config.ddgs_safesearch,
                )

                if raw_results:
                    results = [
                        SearchResult(
                            title=r.get("title", ""),
                            url=r.get("href", r.get("url", "")),
                            content=r.get("body", r.get("description", "")),
                        )
                        for r in raw_results
                    ]
                    logger.info(
                        f"DDGS search succeeded with {backend}: {len(results)} results"
                    )
                    return results

            except Exception as e:
                last_error = e
                logger.warning(f"DDGS {backend} failed: {e}")
                continue

        if last_error:
            logger.error(f"All DDGS backends failed. Last error: {last_error}")

        return []