def _structural_integrity_check(html: str) -> Tuple[bool, str]:
    """
    Tier 3: Structural integrity check for pages that pass pattern detection
    but are structurally broken — incomplete renders, anti-bot redirects, empty shells.

    Only applies to pages < 50KB that aren't JSON/XML.

    Returns:
        Tuple of (is_blocked, reason).
    """
    html_len = len(html)

    # Skip large pages (unlikely to be block pages) and data responses
    if html_len > _STRUCTURAL_MAX_SIZE or _looks_like_data(html):
        return False, ""

    signals = []

    # Signal 1: No <body> tag — definitive structural failure
    if not _BODY_RE.search(html):
        return True, f"Structural: no <body> tag ({html_len} bytes)"

    # Signal 2: Minimal visible text after stripping scripts/styles/tags
    body_match = re.search(r'<body\b[^>]*>([\s\S]*)</body>', html, re.IGNORECASE)
    body_content = body_match.group(1) if body_match else html
    stripped = _SCRIPT_BLOCK_RE.sub('', body_content)
    stripped = _STYLE_TAG_RE.sub('', stripped)
    visible_text = _TAG_RE.sub('', stripped).strip()
    visible_len = len(visible_text)
    if visible_len < 50:
        signals.append("minimal_text")

    # Signal 3: No content elements (semantic HTML)
    content_elements = len(_CONTENT_ELEMENTS_RE.findall(html))
    if content_elements == 0:
        signals.append("no_content_elements")

    # Signal 4: Script-heavy shell — scripts present but no content
    script_count = len(_SCRIPT_TAG_RE.findall(html))
    if script_count > 0 and content_elements == 0 and visible_len < 100:
        signals.append("script_heavy_shell")

    # Scoring
    signal_count = len(signals)
    if signal_count >= 2:
        return True, f"Structural: {', '.join(signals)} ({html_len} bytes, {visible_len} chars visible)"

    if signal_count == 1 and html_len < 5000:
        return True, f"Structural: {signals[0]} on small page ({html_len} bytes, {visible_len} chars visible)"

    return False, ""