async def _iter_sitemap(self, url: str):
        try:
            r = await self.client.get(url, timeout=15, follow_redirects=True)
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            self._log("warning", "Failed to fetch sitemap {url}: HTTP {status_code}",
                      params={"url": url, "status_code": e.response.status_code}, tag="URL_SEED")
            return
        except httpx.RequestError as e:
            self._log("warning", "Network error fetching sitemap {url}: {error}",
                      params={"url": url, "error": str(e)}, tag="URL_SEED")
            return
        except Exception as e:
            self._log("error", "Unexpected error fetching sitemap {url}: {error}",
                      params={"url": url, "error": str(e)}, tag="URL_SEED")
            return

        data = gzip.decompress(r.content) if url.endswith(".gz") else r.content
        base_url = str(r.url)

        def _normalize_loc(raw: Optional[str]) -> Optional[str]:
            if not raw:
                return None
            cleaned = raw.strip().replace("\u200b", "").replace("\ufeff", "")
            normalized = urljoin(base_url, cleaned)
            if not normalized:
                return None
            return normalized

        # Detect if this is a sitemap index by checking for <sitemapindex> or presence of <sitemap> elements
        is_sitemap_index = False
        sub_sitemaps = []
        regular_urls = []

        # Use lxml for XML parsing if available, as it's generally more robust
        if LXML:
            try:
                # Use XML parser for sitemaps, not HTML parser
                parser = etree.XMLParser(recover=True)
                root = etree.fromstring(data, parser=parser)
                # Namespace-agnostic lookups using local-name() so we honor custom or missing namespaces
                sitemap_loc_nodes = root.xpath("//*[local-name()='sitemap']/*[local-name()='loc']")
                url_loc_nodes = root.xpath("//*[local-name()='url']/*[local-name()='loc']")

                self._log(
                    "debug",
                    "Parsed sitemap {url}: {sitemap_count} sitemap entries, {url_count} url entries discovered",
                    params={
                        "url": url,
                        "sitemap_count": len(sitemap_loc_nodes),
                        "url_count": len(url_loc_nodes),
                    },
                    tag="URL_SEED",
                )

                # Check for sitemap index entries
                if sitemap_loc_nodes:
                    is_sitemap_index = True
                    for sitemap_elem in sitemap_loc_nodes:
                        loc = _normalize_loc(sitemap_elem.text)
                        if loc:
                            sub_sitemaps.append(loc)

                # If not a sitemap index, get regular URLs
                if not is_sitemap_index:
                    for loc_elem in url_loc_nodes:
                        loc = _normalize_loc(loc_elem.text)
                        if loc:
                            regular_urls.append(loc)
                    if not regular_urls:
                        self._log(
                            "warning",
                            "No <loc> entries found inside <url> tags for sitemap {url}. The sitemap might be empty or use an unexpected structure.",
                            params={"url": url},
                            tag="URL_SEED",
                        )
            except Exception as e:
                self._log("error", "LXML parsing error for sitemap {url}: {error}",
                          params={"url": url, "error": str(e)}, tag="URL_SEED")
                return
        else:  # Fallback to xml.etree.ElementTree
            import xml.etree.ElementTree as ET
            try:
                # Parse the XML
                root = ET.fromstring(data)
                # Remove namespace from tags for easier processing
                for elem in root.iter():
                    if '}' in elem.tag:
                        elem.tag = elem.tag.split('}')[1]

                # Check for sitemap index entries
                sitemaps = root.findall('.//sitemap')
                url_entries = root.findall('.//url')
                self._log(
                    "debug",
                    "ElementTree parsed sitemap {url}: {sitemap_count} sitemap entries, {url_count} url entries discovered",
                    params={
                        "url": url,
                        "sitemap_count": len(sitemaps),
                        "url_count": len(url_entries),
                    },
                    tag="URL_SEED",
                )
                if sitemaps:
                    is_sitemap_index = True
                    for sitemap in sitemaps:
                        loc_elem = sitemap.find('loc')
                        loc = _normalize_loc(loc_elem.text if loc_elem is not None else None)
                        if loc:
                            sub_sitemaps.append(loc)

                # If not a sitemap index, get regular URLs
                if not is_sitemap_index:
                    for url_elem in url_entries:
                        loc_elem = url_elem.find('loc')
                        loc = _normalize_loc(loc_elem.text if loc_elem is not None else None)
                        if loc:
                            regular_urls.append(loc)
                    if not regular_urls:
                        self._log(
                            "warning",
                            "No <loc> entries found inside <url> tags for sitemap {url}. The sitemap might be empty or use an unexpected structure.",
                            params={"url": url},
                            tag="URL_SEED",
                        )
            except Exception as e:
                self._log("error", "ElementTree parsing error for sitemap {url}: {error}",
                          params={"url": url, "error": str(e)}, tag="URL_SEED")
                return

        # Process based on type
        if is_sitemap_index and sub_sitemaps:
            self._log("info", "Processing sitemap index with {count} sub-sitemaps in parallel",
                      params={"count": len(sub_sitemaps)}, tag="URL_SEED")

            # Create a bounded queue for results to prevent RAM issues
            # For sitemap indexes, use a larger queue as we expect many URLs
            queue_size = min(50000, len(sub_sitemaps) * 1000)  # Estimate 1000 URLs per sitemap
            result_queue = asyncio.Queue(maxsize=queue_size)
            completed_count = 0
            total_sitemaps = len(sub_sitemaps)

            async def process_subsitemap(sitemap_url: str):
                try:
                    self._log(
                        "debug", "Processing sub-sitemap: {url}", params={"url": sitemap_url}, tag="URL_SEED")
                    # Recursively process sub-sitemap
                    async for u in self._iter_sitemap(sitemap_url):
                        await result_queue.put(u)  # Will block if queue is full
                except Exception as e:
                    self._log("error", "Error processing sub-sitemap {url}: {error}",
                              params={"url": sitemap_url, "error": str(e)}, tag="URL_SEED")
                finally:
                    # Put sentinel to signal completion
                    await result_queue.put(None)

            # Start all tasks
            tasks = [asyncio.create_task(process_subsitemap(sm))
                     for sm in sub_sitemaps]

            # Yield results as they come in
            while completed_count < total_sitemaps:
                item = await result_queue.get()
                if item is None:
                    completed_count += 1
                else:
                    yield item

            # Ensure all tasks are done
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Regular sitemap - yield URLs directly
            for u in regular_urls:
                yield u