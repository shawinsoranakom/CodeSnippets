def _read_feed(self, require_entries: bool) -> Any:
        if self._cached_feed is not None:
            if require_entries and not self._cached_feed.entries:
                raise ValueError("RSS feed contains no entries")
            return self._cached_feed

        self._validate_feed_url()

        response = requests.get(self.feed_url, timeout=REQUEST_TIMEOUT_SECONDS, allow_redirects=True)
        response.raise_for_status()

        final_url = getattr(response, "url", self.feed_url)
        if final_url != self.feed_url and urlparse(final_url).hostname:
            _validate_url_no_ssrf(final_url)

        feed = feedparser.parse(response.content)
        if getattr(feed, "bozo", False) and not feed.entries:
            error = getattr(feed, "bozo_exception", None)
            if error:
                raise ValueError(f"Failed to parse RSS feed: {error}") from error
            raise ValueError("Failed to parse RSS feed")
        if require_entries and not feed.entries:
            raise ValueError("RSS feed contains no entries")

        self._cached_feed = feed
        return feed