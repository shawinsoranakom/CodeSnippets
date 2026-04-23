def match_request(self, method, url, params=None):
        """Test if response answers request."""
        if method.lower() != self.method.lower():
            return False

        # regular expression matching
        if isinstance(self._url, RETYPE):
            return self._url.search(str(url)) is not None

        if (
            self._url.scheme != url.scheme
            or self._url.raw_host != url.raw_host
            or self._url.raw_path != url.raw_path
        ):
            return False

        # Ensure all query components in matcher are present in the request
        request_qs = parse_qs(url.query_string)
        matcher_qs = parse_qs(self._url.query_string)
        for key, vals in matcher_qs.items():
            for val in vals:
                try:
                    request_qs.get(key, []).remove(val)
                except ValueError:
                    return False

        return True