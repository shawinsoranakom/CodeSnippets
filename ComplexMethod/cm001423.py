def web_search(self, query: str, num_results: int = 8) -> str:
        """
        Search the web using the best available provider.

        Automatically selects provider: Tavily > Serper > DDGS (multi-engine)

        Args:
            query: The search query
            num_results: Number of results to return (default: 8)

        Returns:
            Formatted search results with optional AI summary
        """
        provider = self._get_provider()
        results: list[SearchResult] = []
        answer: Optional[str] = None

        # Try primary provider
        try:
            if provider == SearchProvider.TAVILY:
                results, answer = self._search_tavily(
                    query,
                    num_results,
                    include_answer=self.config.tavily_include_answer,
                )
            elif provider == SearchProvider.SERPER:
                results = self._search_serper(query, num_results)
            else:
                results = self._search_ddgs(query, num_results)

        except Exception as e:
            logger.warning(f"{provider.value} search failed: {e}, trying fallback...")

            # Fallback chain
            if provider == SearchProvider.TAVILY and self.config.serper_api_key:
                try:
                    results = self._search_serper(query, num_results)
                    provider = SearchProvider.SERPER
                except Exception as e2:
                    logger.warning(f"Serper fallback failed: {e2}")

            if not results:
                logger.info("Falling back to DDGS multi-engine search")
                results = self._search_ddgs(query, num_results)
                provider = SearchProvider.DDGS

        if not results:
            return "No search results found."

        logger.info(f"Search completed using {provider.value}: {len(results)} results")
        return self._format_results(results, answer)