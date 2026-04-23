async def _crawl_batch(self, links_with_scores: List[Tuple[Link, float]], query: str) -> List[CrawlResult]:
        """Crawl multiple URLs in parallel"""
        tasks = []
        for link, score in links_with_scores:
            task = self._crawl_with_preview(link.href, query)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and failed crawls
        valid_results = []
        for result in results:
            if isinstance(result, CrawlResult):
                # Only include successful crawls
                if hasattr(result, 'success') and result.success:
                    valid_results.append(result)
                else:
                    print(f"Skipping failed crawl: {result.url if hasattr(result, 'url') else 'unknown'}")
            elif isinstance(result, Exception):
                print(f"Error in batch crawl: {result}")

        return valid_results