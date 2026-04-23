def quick_extract_links(html: str, base_url: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Fast link extraction for prefetch mode.
    Only extracts <a href> tags - no media, no cleaning, no heavy processing.

    Args:
        html: Raw HTML string
        base_url: Base URL for resolving relative links

    Returns:
        {"internal": [{"href": "...", "text": "..."}], "external": [...]}
    """
    from lxml.html import document_fromstring

    try:
        doc = document_fromstring(html)
    except Exception:
        return {"internal": [], "external": []}

    base_domain = get_base_domain(base_url)
    internal: List[Dict[str, str]] = []
    external: List[Dict[str, str]] = []
    seen: Set[str] = set()

    for a in doc.xpath("//a[@href]"):
        href = a.get("href", "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        # Normalize URL
        normalized = normalize_url_for_deep_crawl(href, base_url)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)

        # Extract text (truncated for memory efficiency)
        text = (a.text_content() or "").strip()[:200]

        link_data = {"href": normalized, "text": text}

        if is_external_url(normalized, base_domain):
            external.append(link_data)
        else:
            internal.append(link_data)

    return {"internal": internal, "external": external}