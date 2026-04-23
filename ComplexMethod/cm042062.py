async def _search_and_rank_urls(
        self, topic: str, query: str, num_results: int = 4, max_num_results: int = None
    ) -> list[str]:
        """Search and rank URLs based on a query.

        Args:
            topic: The research topic.
            query: The search query.
            num_results: The number of URLs to collect.
            max_num_results: The max number of URLs to collect.

        Returns:
            A list of ranked URLs.
        """
        max_results = max_num_results or max(num_results * 2, 6)
        results = await self._search_urls(query, max_results=max_results)
        if len(results) == 0:
            return []
        _results = "\n".join(f"{i}: {j}" for i, j in zip(range(max_results), results))
        time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = COLLECT_AND_RANKURLS_PROMPT.format(topic=topic, query=query, results=_results, time_stamp=time_stamp)
        logger.debug(prompt)
        indices = await self._aask(prompt)
        try:
            indices = OutputParser.extract_struct(indices, list)
            assert all(isinstance(i, int) for i in indices)
        except Exception as e:
            logger.exception(f"fail to rank results for {e}")
            indices = list(range(max_results))
        results = [results[i] for i in indices]
        if self.rank_func:
            results = self.rank_func(results)
        return [i["link"] for i in results[:num_results]]