async def _from_sitemaps(self, domain: str, pattern: str, force: bool = False):
        """
        Discover URLs from sitemaps with smart TTL-based caching.

        1. Check cache validity (TTL + lastmod)
        2. If valid, yield from cache
        3. If invalid or force=True, fetch fresh and update cache
        4. FALLBACK: If anything fails, bypass cache and fetch directly
        """
        # Get config values (passed via self during urls() call)
        cache_ttl_hours = getattr(self, '_cache_ttl_hours', 24)
        validate_lastmod = getattr(self, '_validate_sitemap_lastmod', True)

        # Cache file path (new format: .json instead of .jsonl)
        host = re.sub(r'^https?://', '', domain).rstrip('/')
        host_safe = re.sub('[/?#]+', '_', host)
        digest = hashlib.md5(pattern.encode()).hexdigest()[:8]
        cache_path = self.cache_dir / f"sitemap_{host_safe}_{digest}.json"

        # Check for old .jsonl format and delete it
        old_cache_path = self.cache_dir / f"sitemap_{host_safe}_{digest}.jsonl"
        if old_cache_path.exists():
            try:
                old_cache_path.unlink()
                self._log("info", "Deleted old cache format: {p}",
                          params={"p": str(old_cache_path)}, tag="URL_SEED")
            except Exception:
                pass

        # Step 1: Find sitemap URL and get lastmod (needed for validation)
        sitemap_url = None
        sitemap_lastmod = None
        sitemap_content = None

        schemes = ('https', 'http')
        for scheme in schemes:
            for suffix in ("/sitemap.xml", "/sitemap_index.xml"):
                sm = f"{scheme}://{host}{suffix}"
                resolved = await self._resolve_head(sm)
                if resolved:
                    sitemap_url = resolved
                    # Fetch sitemap content to get lastmod
                    try:
                        r = await self.client.get(sitemap_url, timeout=15, follow_redirects=True)
                        if 200 <= r.status_code < 300:
                            sitemap_content = r.content
                            sitemap_lastmod = _parse_sitemap_lastmod(sitemap_content)
                    except Exception:
                        pass
                    break
            if sitemap_url:
                break

        # Step 2: Check cache validity (skip if force=True)
        if not force and cache_path.exists():
            if _is_cache_valid(cache_path, cache_ttl_hours, validate_lastmod, sitemap_lastmod):
                self._log("info", "Loading sitemap URLs from valid cache: {p}",
                          params={"p": str(cache_path)}, tag="URL_SEED")
                cached_urls = _read_cache(cache_path)
                for url in cached_urls:
                    if _match(url, pattern):
                        yield url
                return
            else:
                self._log("info", "Cache invalid/expired, refetching sitemap for {d}",
                          params={"d": domain}, tag="URL_SEED")

        # Step 3: Fetch fresh URLs
        discovered_urls = []

        if sitemap_url and sitemap_content:
            self._log("info", "Found sitemap at {url}", params={"url": sitemap_url}, tag="URL_SEED")

            # Parse sitemap (reuse content we already fetched)
            async for u in self._iter_sitemap_content(sitemap_url, sitemap_content):
                discovered_urls.append(u)
                if _match(u, pattern):
                    yield u
        elif sitemap_url:
            # We have a sitemap URL but no content (fetch failed earlier), try again
            self._log("info", "Found sitemap at {url}", params={"url": sitemap_url}, tag="URL_SEED")
            async for u in self._iter_sitemap(sitemap_url):
                discovered_urls.append(u)
                if _match(u, pattern):
                    yield u
        else:
            # Fallback: robots.txt
            robots = f"https://{host}/robots.txt"
            try:
                r = await self.client.get(robots, timeout=10, follow_redirects=True)
                if 200 <= r.status_code < 300:
                    sitemap_lines = [l.split(":", 1)[1].strip()
                                     for l in r.text.splitlines()
                                     if l.lower().startswith("sitemap:")]
                    for sm in sitemap_lines:
                        async for u in self._iter_sitemap(sm):
                            discovered_urls.append(u)
                            if _match(u, pattern):
                                yield u
                else:
                    self._log("warning", "robots.txt unavailable for {d} HTTP{c}",
                              params={"d": domain, "c": r.status_code}, tag="URL_SEED")
                    return
            except Exception as e:
                self._log("warning", "Failed to fetch robots.txt for {d}: {e}",
                          params={"d": domain, "e": str(e)}, tag="URL_SEED")
                return

        # Step 4: Write to cache (FALLBACK: if write fails, URLs still yielded above)
        if discovered_urls:
            _write_cache(cache_path, discovered_urls, sitemap_url or "", sitemap_lastmod)
            self._log("info", "Cached {count} URLs for {d}",
                      params={"count": len(discovered_urls), "d": domain}, tag="URL_SEED")