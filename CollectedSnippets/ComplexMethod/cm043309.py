async def _fetch_head(
        self,
        url: str,
        timeout: int,
        max_redirects: int = 5,
        max_bytes: int = 65_536,  # stop after 64 kB even if </head> never comes
        chunk_size: int = 4096,       # how much we read per await
    ):
        for _ in range(max_redirects+1):
            try:
                # ask the first `max_bytes` and force plain text to avoid
                # partial-gzip decode headaches
                async with self.client.stream(
                    "GET",
                    url,
                    timeout=timeout,
                    headers={
                        # "Range": f"bytes=0-{max_bytes-1}", # Dropped the Range header – no need now, and some servers ignore it. We still keep an upper‐bound max_bytes as a fail-safe.
                        "Accept-Encoding": "identity",
                    },
                    follow_redirects=False,
                ) as r:

                    if r.status_code in (301, 302, 303, 307, 308):
                        location = r.headers.get("Location")
                        if location:
                            url = urljoin(url, location)
                            self._log("debug", "Redirecting from {original_url} to {new_url}",
                                      params={"original_url": r.url, "new_url": url}, tag="URL_SEED")
                            continue
                        else:
                            self._log("warning", "Redirect status {status_code} but no Location header for {url}",
                                      params={"status_code": r.status_code, "url": r.url}, tag="URL_SEED")
                            # Return original URL if no new location
                            return False, "", str(r.url)

                    # For 2xx or other non-redirect codes, proceed to read content
                    # Only allow successful codes, or continue
                    if not (200 <= r.status_code < 400):
                        self._log("warning", "Non-success status {status_code} when fetching head for {url}",
                                  params={"status_code": r.status_code, "url": r.url}, tag="URL_SEED")
                        return False, "", str(r.url)

                    buf = bytearray()
                    async for chunk in r.aiter_bytes(chunk_size):
                        buf.extend(chunk)
                        low = buf.lower()
                        if b"</head>" in low or len(buf) >= max_bytes:
                            await r.aclose()
                            break

                    enc = r.headers.get("Content-Encoding", "").lower()
                    try:
                        if enc == "gzip" and buf[:2] == b"\x1f\x8b":
                            buf = gzip.decompress(buf)
                        elif enc == "br" and HAS_BROTLI and buf[:4] == b"\x8b\x6c\x0a\x1a":
                            buf = brotli.decompress(buf)
                        elif enc in {"gzip", "br"}:
                            # Header says “gzip” or “br” but payload is plain – ignore
                            self._log(
                                "debug",
                                "Skipping bogus {encoding} for {url}",
                                params={"encoding": enc, "url": r.url},
                                tag="URL_SEED",
                            )
                    except Exception as e:
                        self._log(
                            "warning",
                            "Decompression error for {url} ({encoding}): {error}",
                            params={"url": r.url,
                                    "encoding": enc, "error": str(e)},
                            tag="URL_SEED",
                        )
                        # fall through with raw buf

                    # Find the </head> tag case-insensitively and decode
                    idx = buf.lower().find(b"</head>")
                    if idx == -1:
                        self._log("debug", "No </head> tag found in initial bytes of {url}",
                                  params={"url": r.url}, tag="URL_SEED")
                        # If no </head> is found, take a reasonable chunk or all if small
                        # Take max 10KB if no head tag
                        html_bytes = buf if len(buf) < 10240 else buf[:10240]
                    else:
                        html_bytes = buf[:idx+7]  # Include </head> tag

                    try:
                        html = html_bytes.decode("utf-8", "replace")
                    except Exception as e:
                        self._log(
                            "warning",
                            "Failed to decode head content for {url}: {error}",
                            params={"url": r.url, "error": str(e)},
                            tag="URL_SEED",
                        )
                        html = html_bytes.decode("latin-1", "replace")

                    # Return the actual URL after redirects
                    return True, html, str(r.url)

            except httpx.RequestError as e:
                self._log("debug", "Fetch head network error for {url}: {error}",
                          params={"url": url, "error": str(e)}, tag="URL_SEED")
                return False, "", url

        # If loop finishes without returning (e.g. too many redirects)
        self._log("warning", "Exceeded max redirects ({max_redirects}) for {url}",
                  params={"max_redirects": max_redirects, "url": url}, tag="URL_SEED")
        return False, "", url