def fetch_json(url: str) -> Any:
    attempts = JSON_FETCH_ATTEMPTS if is_github_api_url(url) else 1
    last_decode_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            data = download_bytes(
                url,
                timeout = 30,
                headers = github_api_headers(url)
                if is_github_api_url(url)
                else auth_headers(url),
            )
        except urllib.error.HTTPError as exc:
            if exc.code == 403 and is_github_api_url(url):
                hint = ""
                if not (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")):
                    hint = (
                        "; set GH_TOKEN or GITHUB_TOKEN to avoid GitHub API rate limits"
                    )
                raise RuntimeError(f"GitHub API returned 403 for {url}{hint}") from exc
            raise
        if not data:
            last_decode_exc = RuntimeError(f"downloaded empty JSON payload from {url}")
        else:
            try:
                payload = json.loads(data.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                last_decode_exc = RuntimeError(
                    f"downloaded invalid JSON from {url}: {exc}"
                )
            else:
                if not isinstance(payload, dict) and not isinstance(payload, list):
                    raise RuntimeError(
                        f"downloaded unexpected JSON type from {url}: {type(payload).__name__}"
                    )
                return payload
        if attempt >= attempts:
            assert last_decode_exc is not None
            raise last_decode_exc
        log(f"json fetch failed ({attempt}/{attempts}) for {url}; retrying")
        sleep_backoff(attempt)
    assert last_decode_exc is not None
    raise last_decode_exc