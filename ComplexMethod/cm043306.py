async def _iter_sitemap_content(self, url: str, content: bytes):
        """Parse sitemap from already-fetched content."""
        data = gzip.decompress(content) if url.endswith(".gz") else content
        base_url = url

        def _normalize_loc(raw: Optional[str]) -> Optional[str]:
            if not raw:
                return None
            cleaned = raw.strip().replace("\u200b", "").replace("\ufeff", "")
            normalized = urljoin(base_url, cleaned)
            if not normalized:
                return None
            return normalized

        # Detect if this is a sitemap index
        is_sitemap_index = False
        sub_sitemaps = []
        regular_urls = []

        if LXML:
            try:
                parser = etree.XMLParser(recover=True)
                root = etree.fromstring(data, parser=parser)
                sitemap_loc_nodes = root.xpath("//*[local-name()='sitemap']/*[local-name()='loc']")
                url_loc_nodes = root.xpath("//*[local-name()='url']/*[local-name()='loc']")

                if sitemap_loc_nodes:
                    is_sitemap_index = True
                    for sitemap_elem in sitemap_loc_nodes:
                        loc = _normalize_loc(sitemap_elem.text)
                        if loc:
                            sub_sitemaps.append(loc)

                if not is_sitemap_index:
                    for loc_elem in url_loc_nodes:
                        loc = _normalize_loc(loc_elem.text)
                        if loc:
                            regular_urls.append(loc)
            except Exception as e:
                self._log("error", "LXML parsing error for sitemap {url}: {error}",
                          params={"url": url, "error": str(e)}, tag="URL_SEED")
                return
        else:
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(data)
                for elem in root.iter():
                    if '}' in elem.tag:
                        elem.tag = elem.tag.split('}')[1]

                sitemaps = root.findall('.//sitemap')
                url_entries = root.findall('.//url')

                if sitemaps:
                    is_sitemap_index = True
                    for sitemap in sitemaps:
                        loc_elem = sitemap.find('loc')
                        loc = _normalize_loc(loc_elem.text if loc_elem is not None else None)
                        if loc:
                            sub_sitemaps.append(loc)

                if not is_sitemap_index:
                    for url_elem in url_entries:
                        loc_elem = url_elem.find('loc')
                        loc = _normalize_loc(loc_elem.text if loc_elem is not None else None)
                        if loc:
                            regular_urls.append(loc)
            except Exception as e:
                self._log("error", "ElementTree parsing error for sitemap {url}: {error}",
                          params={"url": url, "error": str(e)}, tag="URL_SEED")
                return

        # Process based on type
        if is_sitemap_index and sub_sitemaps:
            self._log("info", "Processing sitemap index with {count} sub-sitemaps",
                      params={"count": len(sub_sitemaps)}, tag="URL_SEED")

            queue_size = min(50000, len(sub_sitemaps) * 1000)
            result_queue = asyncio.Queue(maxsize=queue_size)
            completed_count = 0
            total_sitemaps = len(sub_sitemaps)

            async def process_subsitemap(sitemap_url: str):
                try:
                    async for u in self._iter_sitemap(sitemap_url):
                        await result_queue.put(u)
                except Exception as e:
                    self._log("error", "Error processing sub-sitemap {url}: {error}",
                              params={"url": sitemap_url, "error": str(e)}, tag="URL_SEED")
                finally:
                    await result_queue.put(None)

            tasks = [asyncio.create_task(process_subsitemap(sm)) for sm in sub_sitemaps]

            while completed_count < total_sitemaps:
                item = await result_queue.get()
                if item is None:
                    completed_count += 1
                else:
                    yield item

            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            for u in regular_urls:
                yield u