def download_bytes(
    url: str,
    *,
    timeout: int = 120,
    attempts: int = HTTP_FETCH_ATTEMPTS,
    headers: dict[str, str] | None = None,
    progress_label: str | None = None,
) -> bytes:
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers = headers or auth_headers(url))
            with urllib.request.urlopen(request, timeout = timeout) as response:
                total_bytes: int | None = None
                content_length = response.headers.get("Content-Length")
                if content_length and content_length.isdigit():
                    total_bytes = int(content_length)
                progress = (
                    DownloadProgress(progress_label, total_bytes)
                    if progress_label
                    else None
                )
                data = bytearray()
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    data.extend(chunk)
                    if progress is not None:
                        progress.update(len(data))
                if progress is not None:
                    progress.finish(len(data))
                return bytes(data)
        except Exception as exc:
            last_exc = exc
            if attempt >= attempts or not is_retryable_url_error(exc):
                raise
            log(f"fetch failed ({attempt}/{attempts}) for {url}: {exc}; retrying")
            sleep_backoff(attempt)
    assert last_exc is not None
    raise last_exc