async def _crawl_with_preview(self, url: str, query: str) -> Optional[CrawlResult]:
        """Crawl a URL with link preview enabled"""
        config = CrawlerRunConfig(
            link_preview_config=LinkPreviewConfig(
                include_internal=True,
                include_external=False,
                query=query,  # For BM25 scoring
                concurrency=5,
                timeout=5,
                max_links=50,  # Reasonable limit
                verbose=False
            ),
            score_links=True  # Enable intrinsic scoring
        )

        try:
            result = await self.crawler.arun(url=url, config=config)
            # Extract the actual CrawlResult from the container
            if hasattr(result, '_results') and result._results:
                result = result._results[0]

            # Filter our all links do not have head_date
            if hasattr(result, 'links') and result.links:
                result.links['internal'] = [link for link in result.links['internal'] if link.get('head_data')]
                # For now let's ignore external links without head_data
                # result.links['external'] = [link for link in result.links['external'] if link.get('head_data')]

            return result
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None