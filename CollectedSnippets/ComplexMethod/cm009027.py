def detect_url(content: str) -> list[PIIMatch]:
    """Detect URLs in content using regex and stdlib validation.

    Args:
        content: The text content to scan for URLs.

    Returns:
        A list of detected URL matches.
    """
    matches: list[PIIMatch] = []

    # Pattern 1: URLs with scheme (http:// or https://)
    scheme_pattern = r"https?://[^\s<>\"{}|\\^`\[\]]+"

    for match in re.finditer(scheme_pattern, content):
        url = match.group()
        result = urlparse(url)
        if result.scheme in {"http", "https"} and result.netloc:
            matches.append(
                PIIMatch(
                    type="url",
                    value=url,
                    start=match.start(),
                    end=match.end(),
                )
            )

    # Pattern 2: URLs without scheme (www.example.com or example.com/path)
    # More conservative to avoid false positives
    bare_pattern = (
        r"\b(?:www\.)?[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
        r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+(?:/[^\s]*)?"
    )

    for match in re.finditer(bare_pattern, content):
        start, end = match.start(), match.end()
        # Skip if already matched with scheme
        if any(m["start"] <= start < m["end"] or m["start"] < end <= m["end"] for m in matches):
            continue

        url = match.group()
        # Only accept if it has a path or starts with www
        # This reduces false positives like "example.com" in prose
        if "/" in url or url.startswith("www."):
            # Add scheme for validation (required for urlparse to work correctly)
            test_url = f"http://{url}"
            result = urlparse(test_url)
            if result.netloc and "." in result.netloc:
                matches.append(
                    PIIMatch(
                        type="url",
                        value=url,
                        start=start,
                        end=end,
                    )
                )

    return matches