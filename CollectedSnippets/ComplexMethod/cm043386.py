def apply(self, url: str) -> bool:
        """Optimized domain checking with early returns"""
        # Skip processing if no filters
        if not self._blocked_domains and self._allowed_domains is None:
            self._update_stats(True)
            return True

        domain = self._extract_domain(url)

        # Check for blocked domains, including subdomains
        for blocked in self._blocked_domains:
            if self._is_subdomain(domain, blocked):
                self._update_stats(False)
                return False

        # If no allowed domains specified, accept all non-blocked
        if self._allowed_domains is None:
            self._update_stats(True)
            return True

        # Check if domain matches any allowed domain (including subdomains)
        for allowed in self._allowed_domains:
            if self._is_subdomain(domain, allowed):
                self._update_stats(True)
                return True

        # No matches found
        self._update_stats(False)
        return False