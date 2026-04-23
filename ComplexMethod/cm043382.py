async def link_discovery(
        self,
        result: CrawlResult,
        source_url: str,
        current_depth: int,
        _visited: Set[str],
        next_level: List[Tuple[str, Optional[str]]],
        depths: Dict[str, int],
    ) -> None:
        """
        Find the next URLs we should push onto the DFS stack.

        Parameters
        ----------
        result : CrawlResult
            Output of the page we just crawled; its ``links`` block is our raw material.
        source_url : str
            URL of the parent page; stored so callers can track ancestry.
        current_depth : int
            Depth of the parent; children naturally sit at ``current_depth + 1``.
        _visited : Set[str]
            Present to match the BFS signature, but we rely on ``_dfs_seen`` instead.
        next_level : list of tuples
            The stack buffer supplied by the caller; we append new ``(url, parent)`` items here.
        depths : dict
            Shared depth map so future metadata tagging knows how deep each URL lives.

        Notes
        -----
        - ``_dfs_seen`` keeps us from pushing duplicates without touching the traversal guard.
        - Validation, scoring, and capacity trimming mirror the BFS version so behaviour stays consistent.
        """
        next_depth = current_depth + 1
        if next_depth > self.max_depth:
            return

        remaining_capacity = self.max_pages - self._pages_crawled
        if remaining_capacity <= 0:
            self.logger.info(
                f"Max pages limit ({self.max_pages}) reached, stopping link discovery"
            )
            return

        links = result.links.get("internal", [])
        if self.include_external:
            links += result.links.get("external", [])

        seen = self._dfs_seen
        valid_links: List[Tuple[str, float]] = []

        for link in links:
            raw_url = link.get("href")
            if not raw_url:
                continue

            normalized_url = normalize_url_for_deep_crawl(raw_url, source_url)
            if not normalized_url or normalized_url in seen:
                continue

            if not await self.can_process_url(normalized_url, next_depth):
                self.stats.urls_skipped += 1
                continue

            score = self.url_scorer.score(normalized_url) if self.url_scorer else 0
            if score < self.score_threshold:
                self.logger.debug(
                    f"URL {normalized_url} skipped: score {score} below threshold {self.score_threshold}"
                )
                self.stats.urls_skipped += 1
                continue

            seen.add(normalized_url)
            valid_links.append((normalized_url, score))

        if len(valid_links) > remaining_capacity:
            if self.url_scorer:
                valid_links.sort(key=lambda x: x[1], reverse=True)
            valid_links = valid_links[:remaining_capacity]
            self.logger.info(
                f"Limiting to {remaining_capacity} URLs due to max_pages limit"
            )

        for url, score in valid_links:
            if score:
                result.metadata = result.metadata or {}
                result.metadata["score"] = score
            next_level.append((url, source_url))
            depths[url] = next_depth