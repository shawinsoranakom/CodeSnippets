async def _validate(self, url: str, res_list: List[Dict[str, Any]], live: bool,
                        extract: bool, timeout: int, verbose: bool, query: Optional[str] = None,
                        score_threshold: Optional[float] = None, scoring_method: str = "bm25",
                        filter_nonsense: bool = True):
        # Local verbose parameter for this function is used to decide if intermediate logs should be printed
        # The main logger's verbose status should be controlled by the caller.

        # First check if this is a nonsense URL (if filtering is enabled)
        if filter_nonsense and self._is_nonsense_url(url):
            self._log("debug", "Filtered out nonsense URL: {url}", 
                      params={"url": url}, tag="URL_SEED")
            return

        cache_kind = "head" if extract else "live"

        # ---------- try cache ----------
        if not (hasattr(self, 'force') and self.force):
            cached = await self._cache_get(cache_kind, url)
            if cached:
                res_list.append(cached)
                return

        if extract:
            self._log("debug", "Fetching head for {url}", params={
                      "url": url}, tag="URL_SEED")
            ok, html, final = await self._fetch_head(url, timeout)
            status = "valid" if ok else "not_valid"
            self._log("info" if ok else "warning", "HEAD {status} for {final_url}",
                      params={"status": status.upper(), "final_url": final or url}, tag="URL_SEED")
            # head_data = _parse_head(html) if ok else {}
            head_data = await asyncio.to_thread(_parse_head, html) if ok else {}
            entry = {
                "url": final or url,
                "original_url": url,
                "status": status,
                "head_data": head_data,
            }

        elif live:
            self._log("debug", "Performing live check for {url}", params={
                      "url": url}, tag="URL_SEED")
            ok = await self._resolve_head(url)
            status = "valid" if ok else "not_valid"
            self._log("info" if ok else "warning", "LIVE CHECK {status} for {url}",
                      params={"status": status.upper(), "url": url}, tag="URL_SEED")
            entry = {"url": url, "status": status, "head_data": {}}

        else:
            entry = {"url": url, "status": "unknown", "head_data": {}}

        # Add entry to results (scoring will be done later)
        if live or extract:
            await self._cache_set(cache_kind, url, entry)
        res_list.append(entry)