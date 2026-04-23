async def acache_url(self, result: CrawlResult):
        """Cache CrawlResult data"""
        # Store content files and get hashes
        content_map = {
            "html": (result.html, "html"),
            "cleaned_html": (result.cleaned_html or "", "cleaned"),
            "markdown": None,
            "extracted_content": (result.extracted_content or "", "extracted"),
            "screenshot": (result.screenshot or "", "screenshots"),
        }

        try:
            if isinstance(result.markdown, StringCompatibleMarkdown):
                content_map["markdown"] = (
                    result.markdown,
                    "markdown",
                )
            elif isinstance(result.markdown, MarkdownGenerationResult):
                content_map["markdown"] = (
                    result.markdown.model_dump_json(),
                    "markdown",
                )
            elif isinstance(result.markdown, str):
                markdown_result = MarkdownGenerationResult(raw_markdown=result.markdown)
                content_map["markdown"] = (
                    markdown_result.model_dump_json(),
                    "markdown",
                )
            else:
                content_map["markdown"] = (
                    MarkdownGenerationResult().model_dump_json(),
                    "markdown",
                )
        except Exception as e:
            self.logger.warning(
                message=f"Error processing markdown content: {str(e)}", tag="WARNING"
            )
            # Fallback to empty markdown result
            content_map["markdown"] = (
                MarkdownGenerationResult().model_dump_json(),
                "markdown",
            )

        content_hashes = {}
        for field, (content, content_type) in content_map.items():
            content_hashes[field] = await self._store_content(content, content_type)

        # Extract cache validation headers from response
        response_headers = result.response_headers or {}
        etag = response_headers.get("etag") or response_headers.get("ETag") or ""
        last_modified = response_headers.get("last-modified") or response_headers.get("Last-Modified") or ""
        # head_fingerprint is set by caller via result attribute (if available)
        head_fingerprint = getattr(result, "head_fingerprint", None) or ""
        cached_at = time.time()

        async def _cache(db):
            await db.execute(
                """
                INSERT INTO crawled_data (
                    url, html, cleaned_html, markdown,
                    extracted_content, success, media, links, metadata,
                    screenshot, response_headers, downloaded_files,
                    etag, last_modified, head_fingerprint, cached_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    html = excluded.html,
                    cleaned_html = excluded.cleaned_html,
                    markdown = excluded.markdown,
                    extracted_content = excluded.extracted_content,
                    success = excluded.success,
                    media = excluded.media,
                    links = excluded.links,
                    metadata = excluded.metadata,
                    screenshot = excluded.screenshot,
                    response_headers = excluded.response_headers,
                    downloaded_files = excluded.downloaded_files,
                    etag = excluded.etag,
                    last_modified = excluded.last_modified,
                    head_fingerprint = excluded.head_fingerprint,
                    cached_at = excluded.cached_at
            """,
                (
                    result.url,
                    content_hashes["html"],
                    content_hashes["cleaned_html"],
                    content_hashes["markdown"],
                    content_hashes["extracted_content"],
                    result.success,
                    json.dumps(result.media),
                    json.dumps(result.links),
                    json.dumps(result.metadata or {}),
                    content_hashes["screenshot"],
                    json.dumps(result.response_headers or {}),
                    json.dumps(result.downloaded_files or []),
                    etag,
                    last_modified,
                    head_fingerprint,
                    cached_at,
                ),
            )

        try:
            await self.execute_with_retry(_cache)
        except Exception as e:
            self.logger.error(
                message="Error caching URL: {error}",
                tag="ERROR",
                force_verbose=True,
                params={"error": str(e)},
            )