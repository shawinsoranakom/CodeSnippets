async def _resolve_head(self, url: str) -> Optional[str]:
        """
        HEAD-probe a URL.

        Returns:
            * the same URL if it answers 2xx,
            * the verified absolute redirect target if it answers 3xx
              and the target also answers 2xx,
            * None on any other status or network error.
        """
        try:
            r = await self.client.head(url, timeout=10, follow_redirects=False)

            # direct hit
            if 200 <= r.status_code < 300:
                return str(r.url)

            # single level redirect — verify target is alive
            if r.status_code in (301, 302, 303, 307, 308):
                loc = r.headers.get("location")
                if loc:
                    target = urljoin(url, loc)
                    # Guard against self-redirects
                    if target == url:
                        return None
                    try:
                        r2 = await self.client.head(
                            target, timeout=10, follow_redirects=False
                        )
                        if 200 <= r2.status_code < 300:
                            return str(r2.url)
                    except Exception:
                        pass
                    return None

            return None

        except Exception as e:
            self._log("debug", "HEAD {url} failed: {err}",
                      params={"url": url, "err": str(e)}, tag="URL_SEED")
            return None