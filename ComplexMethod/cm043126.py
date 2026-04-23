def score_link(self, link: Link, query: str, state: CrawlState) -> float:
        """Custom link scoring for API documentation"""
        score = 1.0
        url = link.href.lower()

        # Boost API-related URLs
        for pattern in self.valuable_patterns:
            if re.search(pattern, url):
                score *= 2.0
                break

        # Reduce score for non-API content
        for pattern in self.avoid_patterns:
            if re.search(pattern, url):
                score *= 0.1
                break

        # Boost if preview contains API keywords
        if link.text:
            preview_lower = link.text.lower()
            keyword_count = sum(1 for kw in self.api_keywords if kw in preview_lower)
            score *= (1 + keyword_count * 0.2)

        # Prioritize shallow URLs (likely overview pages)
        depth = url.count('/') - 2  # Subtract protocol slashes
        if depth <= 3:
            score *= 1.5
        elif depth > 6:
            score *= 0.5

        return score