async def crawl(
        self, 
        url: str, 
        config: Optional[CrawlerRunConfig] = None, 
        **kwargs
    ) -> AsyncCrawlResponse:
        config = config or CrawlerRunConfig.from_kwargs(kwargs)

        parsed = urlparse(url)
        scheme = parsed.scheme.rstrip('/')

        if scheme not in self.VALID_SCHEMES:
            raise ValueError(f"Unsupported URL scheme: {scheme}")

        try:
            if scheme == 'file':
                return await self._handle_file(parsed.path)
            elif scheme == 'raw':
                # Don't use parsed.path - urlparse truncates at '#' which is common in CSS
                # Strip prefix directly: "raw://" (6 chars) or "raw:" (4 chars)
                raw_content = url[6:] if url.startswith("raw://") else url[4:]
                return await self._handle_raw(raw_content, base_url=config.base_url)
            else:  # http or https
                return await self._handle_http(url, config)

        except Exception as e:
            if self.logger:
                self.logger.error(
                    message="Crawl failed: {error}",
                    tag="CRAWL",
                    params={"error": str(e), "url": url}
                )
            raise