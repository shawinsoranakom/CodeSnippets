async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        url: str = "",
        extract_text: bool = True,
        **kwargs: Any,
    ) -> ToolResponseBase:
        url = url.strip()
        session_id = session.session_id if session else None

        if not url:
            return ErrorResponse(
                message="Please provide a URL to fetch.",
                error="missing_url",
                session_id=session_id,
            )

        try:
            client = Requests(raise_for_status=False, retry_max_attempts=1)
            response = await client.get(url, timeout=_REQUEST_TIMEOUT)
        except ValueError as e:
            # validate_url raises ValueError for SSRF / blocked IPs
            return ErrorResponse(
                message=f"URL blocked: {e}",
                error="url_blocked",
                session_id=session_id,
            )
        except Exception as e:
            logger.warning(f"[web_fetch] Request failed for {url}: {e}")
            return ErrorResponse(
                message=f"Failed to fetch URL: {e}",
                error="fetch_failed",
                session_id=session_id,
            )

        content_type = response.headers.get("content-type", "")
        if not _is_text_content(content_type):
            return ErrorResponse(
                message=f"Non-text content type: {content_type.split(';')[0]}",
                error="unsupported_content_type",
                session_id=session_id,
            )

        raw = response.content[:_MAX_CONTENT_BYTES]
        text = raw.decode("utf-8", errors="replace")

        if extract_text and "html" in content_type.lower():
            text = _html_to_text(text)

        return WebFetchResponse(
            message=f"Fetched {url}",
            url=response.url,
            status_code=response.status,
            content_type=content_type.split(";")[0].strip(),
            content=text,
            truncated=False,
            session_id=session_id,
        )