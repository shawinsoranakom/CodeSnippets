async def can_process_url(self, url: str, depth: int) -> bool:
        """
        Validate the URL format and apply filtering.
        For the starting URL (depth 0), filtering is bypassed.
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Missing scheme or netloc")
            if parsed.scheme not in ("http", "https"):
                raise ValueError("Invalid scheme")
            if "." not in parsed.netloc:
                raise ValueError("Invalid domain")
        except Exception as e:
            self.logger.warning(f"Invalid URL: {url}, error: {e}")
            return False

        if depth != 0 and not await self.filter_chain.apply(url):
            return False

        return True