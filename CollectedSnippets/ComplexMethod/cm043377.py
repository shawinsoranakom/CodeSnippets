async def link_discovery(
        self,
        result: CrawlResult,
        source_url: str,
        current_depth: int,
        visited: Set[str],
        next_level: List[Tuple[str, Optional[str]]],
        depths: Dict[str, int],
    ) -> None:
        """
        Extracts links from the crawl result, validates and scores them, and
        prepares the next level of URLs.
        Each valid URL is appended to next_level as a tuple (url, parent_url)
        and its depth is tracked.
        """            
        next_depth = current_depth + 1
        if next_depth > self.max_depth:
            return

        # If we've reached the max pages limit, don't discover new links
        remaining_capacity = self.max_pages - self._pages_crawled
        if remaining_capacity <= 0:
            self.logger.info(f"Max pages limit ({self.max_pages}) reached, stopping link discovery")
            return

        # Get internal links and, if enabled, external links.
        links = result.links.get("internal", [])
        if self.include_external:
            links += result.links.get("external", [])

        valid_links = []

        # First collect all valid links
        for link in links:
            url = link.get("href")
            # Strip URL fragments to avoid duplicate crawling
            # base_url = url.split('#')[0] if url else url
            base_url = normalize_url_for_deep_crawl(url, source_url)
            if base_url in visited:
                continue
            if not await self.can_process_url(base_url, next_depth):
                self.stats.urls_skipped += 1
                continue

            # Score the URL if a scorer is provided
            score = self.url_scorer.score(base_url) if self.url_scorer else 0

            # Skip URLs with scores below the threshold
            if score < self.score_threshold:
                self.logger.debug(f"URL {url} skipped: score {score} below threshold {self.score_threshold}")
                self.stats.urls_skipped += 1
                continue

            visited.add(base_url)
            valid_links.append((base_url, score))

        # If we have more valid links than capacity, sort by score and take the top ones
        if len(valid_links) > remaining_capacity:
            if self.url_scorer:
                # Sort by score in descending order
                valid_links.sort(key=lambda x: x[1], reverse=True)
            # Take only as many as we have capacity for
            valid_links = valid_links[:remaining_capacity]
            self.logger.info(f"Limiting to {remaining_capacity} URLs due to max_pages limit")

        # Process the final selected links
        for url, score in valid_links:
            # attach the score to metadata if needed
            if score:
                result.metadata = result.metadata or {}
                result.metadata["score"] = score
            next_level.append((url, source_url))
            depths[url] = next_depth