def _filter_links(self, links: Links, link_config: Dict[str, Any]) -> List[str]:
        """
        Filter links based on configuration parameters.

        Args:
            links: Links object containing internal and external links
            link_config: Configuration dictionary for link extraction

        Returns:
            List of filtered URL strings
        """
        filtered_urls = []

        # Include internal links if configured
        if link_config.include_internal:
            filtered_urls.extend([link.href for link in links.internal if link.href])
            self._log("debug", "Added {count} internal links",
                      params={"count": len(links.internal)})

        # Include external links if configured
        if link_config.include_external:
            filtered_urls.extend([link.href for link in links.external if link.href])
            self._log("debug", "Added {count} external links",
                      params={"count": len(links.external)})

        # Apply include patterns
        include_patterns = link_config.include_patterns
        if include_patterns:
            filtered_urls = [
                url for url in filtered_urls
                if any(fnmatch.fnmatch(url, pattern) for pattern in include_patterns)
            ]
            self._log("debug", "After include patterns: {count} links remain",
                      params={"count": len(filtered_urls)})

        # Apply exclude patterns
        exclude_patterns = link_config.exclude_patterns
        if exclude_patterns:
            filtered_urls = [
                url for url in filtered_urls
                if not any(fnmatch.fnmatch(url, pattern) for pattern in exclude_patterns)
            ]
            self._log("debug", "After exclude patterns: {count} links remain",
                      params={"count": len(filtered_urls)})

        # Limit number of links
        max_links = link_config.max_links
        if max_links > 0 and len(filtered_urls) > max_links:
            filtered_urls = filtered_urls[:max_links]
            self._log("debug", "Limited to {max_links} links",
                      params={"max_links": max_links})

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in filtered_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        self._log("debug", "Final filtered URLs: {count} unique links",
                  params={"count": len(unique_urls)})

        return unique_urls