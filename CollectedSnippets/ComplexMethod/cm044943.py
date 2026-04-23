def _fetch_latest_release_tag() -> tuple[str | None, str | None]:
    """Return (tag, failure_category). Exactly one outbound call, 5 s timeout.

    On success: (tag_name, None).
    On a documented network/HTTP failure (added in T029/T030): (None, category).
    On anything else — including a malformed response body — the exception
    propagates; there is no catch-all (research D-006).
    """
    req = urllib.request.Request(
        GITHUB_API_LATEST,
        headers={"Accept": "application/vnd.github+json"},
    )
    token = None
    for env_var in ("GH_TOKEN", "GITHUB_TOKEN"):
        candidate = os.environ.get(env_var)
        if candidate is not None:
            candidate = candidate.strip()
            if candidate:
                token = candidate
                break
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            tag = payload.get("tag_name")
            if not isinstance(tag, str) or not tag:
                raise ValueError("GitHub API response missing valid tag_name")
            return tag, None
    except urllib.error.HTTPError as e:
        # Order matters: HTTPError is a subclass of URLError.
        if e.code == 403:
            return None, "rate limited (try setting GH_TOKEN or GITHUB_TOKEN)"
        return None, f"HTTP {e.code}"
    except (urllib.error.URLError, OSError):
        return None, "offline or timeout"