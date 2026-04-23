def is_match(self, url: str) -> bool:
        """Check if this config matches the given URL.

        Args:
            url: The URL to check against this config's matcher

        Returns:
            bool: True if this config should be used for the URL or if no matcher is set.
        """
        if self.url_matcher is None:
            return True

        if callable(self.url_matcher):
            # Single function matcher
            return self.url_matcher(url)

        elif isinstance(self.url_matcher, str):
            # Single pattern string
            from fnmatch import fnmatch
            return fnmatch(url, self.url_matcher)

        elif isinstance(self.url_matcher, list):
            # List of mixed matchers
            if not self.url_matcher:  # Empty list
                return False

            results = []
            for matcher in self.url_matcher:
                if callable(matcher):
                    results.append(matcher(url))
                elif isinstance(matcher, str):
                    from fnmatch import fnmatch
                    results.append(fnmatch(url, matcher))
                else:
                    # Skip invalid matchers
                    continue

            # Apply match mode logic
            if self.match_mode == MatchMode.OR:
                return any(results) if results else False
            else:  # AND mode
                return all(results) if results else False

        return False