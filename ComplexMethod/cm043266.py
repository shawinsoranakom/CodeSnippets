async def _fetch_head(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Fetch only the <head> section of a page.

        Uses streaming to stop reading after </head> is found,
        minimizing bandwidth usage.

        Args:
            url: The URL to fetch

        Returns:
            Tuple of (head_html, etag, last_modified)
        """
        client = await self._get_client()

        try:
            async with client.stream(
                "GET",
                url,
                headers={"Accept-Encoding": "identity"}  # Disable compression for easier parsing
            ) as response:
                etag = response.headers.get("etag")
                last_modified = response.headers.get("last-modified")

                if response.status_code != 200:
                    return None, etag, last_modified

                # Read until </head> or max 64KB
                chunks = []
                total_bytes = 0
                max_bytes = 65536

                async for chunk in response.aiter_bytes(4096):
                    chunks.append(chunk)
                    total_bytes += len(chunk)

                    content = b''.join(chunks)
                    # Check for </head> (case insensitive)
                    if b'</head>' in content.lower() or b'</HEAD>' in content:
                        break
                    if total_bytes >= max_bytes:
                        break

                html = content.decode('utf-8', errors='replace')

                # Extract just the head section
                head_end = html.lower().find('</head>')
                if head_end != -1:
                    html = html[:head_end + 7]

                return html, etag, last_modified

        except Exception:
            return None, None, None