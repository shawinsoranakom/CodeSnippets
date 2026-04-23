async def _from_cc(self, domain: str, pattern: str, force: bool):
        import re
        digest = hashlib.md5(pattern.encode()).hexdigest()[:8]

        # ── normalise for CC   (strip scheme, query, fragment)
        raw = re.sub(r'^https?://', '', domain).split('#',
                                                      1)[0].split('?', 1)[0].lstrip('.')

        # ── sanitize only for cache-file name
        safe = re.sub('[/?#]+', '_', raw)
        path = self.cache_dir / f"{self.index_id}_{safe}_{digest}.jsonl"

        if path.exists() and not force:
            self._log("info", "Loading CC URLs for {domain} from cache: {path}",
                      params={"domain": domain, "path": path}, tag="URL_SEED")
            async with aiofiles.open(path, "r") as fp:
                async for line in fp:
                    url = line.strip()
                    if _match(url, pattern):
                        yield url
            return

        # build CC glob – if a path is present keep it, else add trailing /*
        glob = f"*.{raw}*" if '/' in raw else f"*.{raw}/*"
        url = f"https://index.commoncrawl.org/{self.index_id}-index?url={quote(glob, safe='*')}&output=json"

        retries = (1, 3, 7)
        self._log("info", "Fetching CC URLs for {domain} from Common Crawl index: {url}",
                  params={"domain": domain, "url": url}, tag="URL_SEED")
        for i, d in enumerate(retries+(-1,)):  # last -1 means don't retry
            try:
                async with self.client.stream("GET", url) as r:
                    r.raise_for_status()
                    async with aiofiles.open(path, "w") as fp:
                        async for line in r.aiter_lines():
                            rec = json.loads(line)
                            u = rec["url"]
                            await fp.write(u+"\n")
                            if _match(u, pattern):
                                yield u
                return
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 503 and i < len(retries):
                    self._log("warning", "Common Crawl API returned 503 for {domain}. Retrying in {delay}s.",
                              params={"domain": domain, "delay": retries[i]}, tag="URL_SEED")
                    await asyncio.sleep(retries[i])
                    continue
                self._log("error", "HTTP error fetching CC index for {domain}: {error}",
                          params={"domain": domain, "error": str(e)}, tag="URL_SEED")
                raise
            except Exception as e:
                self._log("error", "Error fetching CC index for {domain}: {error}",
                          params={"domain": domain, "error": str(e)}, tag="URL_SEED")
                raise