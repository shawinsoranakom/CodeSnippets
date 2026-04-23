async def link_discovery(
        self,
        result: CrawlResult,
        source_url: str,
        current_depth: int,
        visited: Set[str],
        next_links: List[Tuple[str, Optional[str]]],
        depths: Dict[str, int],
    ) -> None:
        """
        Extract links from the crawl result, validate them, and append new URLs
        (with their parent references) to next_links.
        Also updates the depths dictionary.
        """
        new_depth = current_depth + 1
        if new_depth > self.max_depth:
            return

        # If we've reached the max pages limit, don't discover new links
        remaining_capacity = self.max_pages - self._pages_crawled
        if remaining_capacity <= 0:
            self.logger.info(f"Max pages limit ({self.max_pages}) reached, stopping link discovery")
            return

        # Retrieve internal links; include external links if enabled.
        links = result.links.get("internal", [])
        if self.include_external:
            links += result.links.get("external", [])

        # If we have more links than remaining capacity, limit how many we'll process
        valid_links = []
        for link in links:
            url = link.get("href")
            base_url = normalize_url_for_deep_crawl(url, source_url)
            if base_url in visited:
                continue
            if not await self.can_process_url(base_url, new_depth):
                self.stats.urls_skipped += 1
                continue

            valid_links.append(base_url)

        # Record the new depths and add to next_links
        for url in valid_links:
            depths[url] = new_depth
            next_links.append((url, source_url))