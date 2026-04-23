def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents = True, exist_ok = True)
    last_exc: Exception | None = None
    for attempt in range(1, HTTP_FETCH_ATTEMPTS + 1):
        tmp_path: Path | None = None
        try:
            request = urllib.request.Request(url, headers = auth_headers(url))
            with tempfile.NamedTemporaryFile(
                prefix = destination.name + ".tmp-",
                dir = destination.parent,
                delete = False,
            ) as handle:
                tmp_path = Path(handle.name)
                with urllib.request.urlopen(request, timeout = 120) as response:
                    total_bytes: int | None = None
                    content_length = response.headers.get("Content-Length")
                    if content_length and content_length.isdigit():
                        total_bytes = int(content_length)
                    progress = DownloadProgress(
                        f"Downloading {destination.name}", total_bytes
                    )
                    downloaded_bytes = 0
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
                        downloaded_bytes += len(chunk)
                        progress.update(downloaded_bytes)
                    progress.finish(downloaded_bytes)
                handle.flush()
                os.fsync(handle.fileno())
            if not tmp_path.exists() or tmp_path.stat().st_size == 0:
                raise RuntimeError(f"downloaded empty file from {url}")
            atomic_replace_from_tempfile(tmp_path, destination)
            return
        except Exception as exc:
            last_exc = exc
            if tmp_path is not None:
                try:
                    tmp_path.unlink(missing_ok = True)
                except Exception:
                    pass
            if attempt >= HTTP_FETCH_ATTEMPTS or not is_retryable_url_error(exc):
                raise
            log(
                f"download failed ({attempt}/{HTTP_FETCH_ATTEMPTS}) for {url}: {exc}; retrying"
            )
            sleep_backoff(attempt)
    assert last_exc is not None
    raise last_exc