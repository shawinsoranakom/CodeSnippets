async def call_endpoint(
        self, 
        method: str, 
        body: Dict[str, Any], 
        is_retry: bool = False,
        use_auth_headers: bool = False
    ) -> Any:
        """
        Call Antigravity API endpoint with JSON body and endpoint fallback.

        Tries each base URL in order until one succeeds.
        Automatically retries once on 401 Unauthorized by refreshing auth.
        """
        if not self.get_access_token():
            await self.initialize_auth()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_access_token()}",
            **(ANTIGRAVITY_AUTH_HEADERS if use_auth_headers else ANTIGRAVITY_HEADERS),
        }

        # Try cached working URL first, then fallback chain
        urls_to_try = []
        if self._working_base_url:
            urls_to_try.append(self._working_base_url)
        urls_to_try.extend([url for url in BASE_URLS if url != self._working_base_url])

        last_error = None
        for base_url in urls_to_try:
            url = f"{base_url}:{method}"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=body, timeout=30) as resp:
                        if resp.status == 401 and not is_retry:
                            # Token likely expired, clear and retry once
                            await self.clear_token_cache()
                            await self.initialize_auth()
                            return await self.call_endpoint(method, body, is_retry=True, use_auth_headers=use_auth_headers)
                        elif resp.ok:
                            self._working_base_url = base_url  # Cache working URL
                            return await resp.json()
                        else:
                            last_error = f"HTTP {resp.status}: {await resp.text()}"
                            debug.log(f"Antigravity endpoint {base_url} returned {resp.status}")
            except Exception as e:
                last_error = str(e)
                debug.log(f"Antigravity endpoint {base_url} failed: {e}")
                continue

        raise RuntimeError(f"All Antigravity endpoints failed. Last error: {last_error}")