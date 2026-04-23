def apply(self, url: str) -> bool:
        url_path = urlparse(url).path

        # Quick suffix check (*.html)
        if self._simple_suffixes:
            if url_path.split("/")[-1].split(".")[-1] in self._simple_suffixes:
                result = True
                self._update_stats(result)
                return not result if self._reverse else result

        # Domain check
        if self._domain_patterns:
            for pattern in self._domain_patterns:
                if pattern.match(url):
                    result = True
                    self._update_stats(result)
                    return not result if self._reverse else result

        # Prefix check (/foo/* or https://domain/foo/*)
        if self._simple_prefixes:
            for prefix in self._simple_prefixes:
                # Use url_path for path-only prefixes, full URL for absolute prefixes
                match_against = url if '://' in prefix else url_path
                if match_against.startswith(prefix):
                    if len(match_against) == len(prefix) or match_against[len(prefix)] in ['/', '?', '#']:
                        result = True
                        self._update_stats(result)
                        return not result if self._reverse else result

        # Complex patterns
        if self._path_patterns:
            if any(p.search(url) for p in self._path_patterns):
                result = True
                self._update_stats(result)
                return not result if self._reverse else result

        result = False
        self._update_stats(result)
        return not result if self._reverse else result