def resolve_platform_uri(uri, hard=True):
    """Resolve ul:// URIs to signed URLs by authenticating with Ultralytics Platform.

    Formats:
        ul://username/datasets/slug  -> Returns signed URL to NDJSON file
        ul://username/project/model  -> Returns signed URL to .pt file

    Args:
        uri (str): Platform URI starting with "ul://".
        hard (bool): Whether to raise an error if resolution fails.

    Returns:
        (str | None): Signed URL on success, None if not found and hard=False.

    Raises:
        ValueError: If API key is missing/invalid or URI format is wrong.
        PermissionError: If access is denied.
        RuntimeError: If resource is not ready (e.g., dataset still processing).
        FileNotFoundError: If resource not found and hard=True.
        ConnectionError: If network request fails and hard=True.
    """
    import requests

    path = uri[5:]  # Remove "ul://"
    parts = path.split("/")

    api_key = os.getenv("ULTRALYTICS_API_KEY") or SETTINGS.get("api_key")
    if not api_key:
        raise ValueError(f"ULTRALYTICS_API_KEY required for '{uri}'. Get key at {PLATFORM_URL}/settings")

    base = PLATFORM_API_URL
    headers = {"Authorization": f"Bearer {api_key}"}

    # ul://username/datasets/slug
    if len(parts) == 3 and parts[1] == "datasets":
        username, _, slug = parts
        url = f"{base}/datasets/{username}/{slug}/export"

    # ul://username/project/model
    elif len(parts) == 3:
        username, project, model = parts
        url = f"{base}/models/{username}/{project}/{model}/download"

    else:
        raise ValueError(f"Invalid platform URI: {uri}. Use ul://user/datasets/name or ul://user/project/model")

    # (connect_timeout, read_timeout) — short connect so retries are fast, long read for server-side generation
    timeout = (10, 3600) if "/datasets/" in url else (10, 90)

    try:
        for attempt in range(5):
            try:
                r = requests.head(url, headers=headers, allow_redirects=False, timeout=timeout)
                if r.status_code in {408, 429} or r.status_code >= 500:
                    raise requests.exceptions.HTTPError(f"HTTP {r.status_code}", response=r)
                break
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.HTTPError,
            ) as e:
                if attempt >= 4:
                    raise
                delay = 2 * (2**attempt)  # 2s, 4s, 8s, 16s backoff
                LOGGER.warning(f"Retry {attempt + 1}/5 for {uri} in {delay}s: {e}")
                sleep(delay)
    except Exception as e:
        if hard:
            raise ConnectionError(f"Failed to resolve {uri}: {e}") from e
        LOGGER.warning(f"Failed to resolve {uri}: {e}")
        return None

    # Handle redirect responses (301, 302, 303, 307, 308)
    if 300 <= r.status_code < 400 and "location" in r.headers:
        return r.headers["location"]  # Return signed URL

    # Handle error responses
    if r.status_code == 401:
        raise ValueError(f"Invalid ULTRALYTICS_API_KEY for '{uri}'")
    if r.status_code == 403:
        raise PermissionError(f"Access denied for '{uri}'. Check dataset/model visibility settings.")
    if r.status_code == 404:
        if hard:
            raise FileNotFoundError(f"Not found on platform: {uri}")
        LOGGER.warning(f"Not found on platform: {uri}")
        return None
    if r.status_code == 409:
        raise RuntimeError(f"Resource not ready: {uri}. Dataset may still be processing.")

    # Unexpected response
    r.raise_for_status()
    raise RuntimeError(f"Unexpected response from platform for '{uri}': {r.status_code}")