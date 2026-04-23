def is_blocked(
    status_code: Optional[int],
    html: str,
    error_message: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Detect if a crawl result indicates anti-bot blocking.

    Uses layered detection to maximize coverage while minimizing false positives:
    - Tier 1 patterns (structural markers) trigger on any page size
    - Tier 2 patterns (generic terms) only trigger on short pages (< 10KB)
    - Tier 3 structural integrity catches silent blocks and empty shells
    - Status-code checks require corroborating content signals

    Args:
        status_code: HTTP status code from the response.
        html: Raw HTML content from the response.
        error_message: Error message from the crawl result, if any.

    Returns:
        Tuple of (is_blocked, reason). reason is empty string when not blocked.
    """
    html = html or ""
    html_len = len(html)

    # --- HTTP 429 is always rate limiting ---
    if status_code == 429:
        return True, "HTTP 429 Too Many Requests"

    # --- Check for tier 1 patterns (high confidence, any page size) ---
    # First check the raw start of the page (fast path for small pages).
    # Then, for large pages, also check a stripped version (scripts/styles
    # removed) because modern block pages bury text under 100KB+ of CSS/JS.
    snippet = html[:15000]
    if snippet:
        for pattern, reason in _TIER1_PATTERNS:
            if pattern.search(snippet):
                return True, reason

    # Large-page deep scan: strip scripts/styles and re-check tier 1
    if html_len > 15000:
        _stripped_for_t1 = _SCRIPT_BLOCK_RE.sub('', html[:500000])
        _stripped_for_t1 = _STYLE_TAG_RE.sub('', _stripped_for_t1)
        _deep_snippet = _stripped_for_t1[:30000]
        for pattern, reason in _TIER1_PATTERNS:
            if pattern.search(_deep_snippet):
                return True, reason

    # --- HTTP 403/503 — always blocked for non-data HTML responses ---
    # Rationale: 403/503 are never the content the user wants. Modern block pages
    # (Reddit, LinkedIn, etc.) serve full SPA shells that exceed 100KB, so
    # size-based filtering misses them. Even for a legitimate auth error, the
    # fallback (Web Unlocker) will also get 403 and we correctly report failure.
    # False positives are cheap — the fallback mechanism rescues them.
    if status_code in (403, 503) and not _looks_like_data(html):
        if html_len < _EMPTY_CONTENT_THRESHOLD:
            return True, f"HTTP {status_code} with near-empty response ({html_len} bytes)"
        # For large pages, strip scripts/styles to find block text in the
        # actual content (Reddit hides it under 180KB of inline CSS).
        # Check tier 2 patterns regardless of page size.
        if html_len > _TIER2_MAX_SIZE:
            _stripped = _SCRIPT_BLOCK_RE.sub('', html[:500000])
            _stripped = _STYLE_TAG_RE.sub('', _stripped)
            _check_snippet = _stripped[:30000]
        else:
            _check_snippet = snippet
        for pattern, reason in _TIER2_PATTERNS:
            if pattern.search(_check_snippet):
                return True, f"{reason} (HTTP {status_code}, {html_len} bytes)"
        # Even without a pattern match, a non-data 403/503 HTML page is
        # almost certainly a block. Flag it so the fallback gets a chance.
        return True, f"HTTP {status_code} with HTML content ({html_len} bytes)"

    # --- Tier 2 patterns on other 4xx/5xx + short page ---
    if status_code and status_code >= 400 and html_len < _TIER2_MAX_SIZE:
        for pattern, reason in _TIER2_PATTERNS:
            if pattern.search(snippet):
                return True, f"{reason} (HTTP {status_code}, {html_len} bytes)"

    # --- HTTP 200 + near-empty content (JS-rendered empty page) ---
    if status_code == 200:
        stripped = html.strip()
        if len(stripped) < _EMPTY_CONTENT_THRESHOLD and not _looks_like_data(html):
            return True, f"Near-empty content ({len(stripped)} bytes) with HTTP 200"

    # --- Tier 3: Structural integrity (catches silent blocks, redirects, incomplete renders) ---
    _blocked, _reason = _structural_integrity_check(html)
    if _blocked:
        return True, _reason

    return False, ""