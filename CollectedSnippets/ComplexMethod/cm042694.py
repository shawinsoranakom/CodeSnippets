def _compute_freshness_lifetime(
        self, response: Response, request: Request, now: float
    ) -> float:
        # Reference nsHttpResponseHead::ComputeFreshnessLifetime
        # https://dxr.mozilla.org/mozilla-central/source/netwerk/protocol/http/nsHttpResponseHead.cpp#706
        cc = self._parse_cachecontrol(response)
        maxage = self._get_max_age(cc)
        if maxage is not None:
            return maxage

        # Parse date header or synthesize it if none exists
        date = rfc1123_to_epoch(response.headers.get(b"Date")) or now

        # Try HTTP/1.0 Expires header
        if b"Expires" in response.headers:
            expires = rfc1123_to_epoch(response.headers[b"Expires"])
            # When parsing Expires header fails RFC 2616 section 14.21 says we
            # should treat this as an expiration time in the past.
            return max(0, expires - date) if expires else 0

        # Fallback to heuristic using last-modified header
        # This is not in RFC but on Firefox caching implementation
        lastmodified = rfc1123_to_epoch(response.headers.get(b"Last-Modified"))
        if lastmodified and lastmodified <= date:
            return (date - lastmodified) / 10

        # This request can be cached indefinitely
        if response.status in {300, 301, 308}:
            return self.MAXAGE

        # Insufficient information to compute freshness lifetime
        return 0