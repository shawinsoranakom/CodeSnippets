def efficient_normalize_url_for_deep_crawl(href, base_url, preserve_https=False, original_scheme=None):
    """Efficient URL normalization with proper parsing"""
    from urllib.parse import urljoin

    if not href:
        return None

    # Resolve relative URLs
    full_url = urljoin(base_url, href.strip())

    # Preserve HTTPS if requested and original scheme was HTTPS
    if preserve_https and original_scheme == 'https':
        parsed_full = urlparse(full_url)
        parsed_base = urlparse(base_url)
        # Only preserve HTTPS for same-domain links (not protocol-relative URLs)
        # Protocol-relative URLs (//example.com) should follow the base URL's scheme
        if (parsed_full.scheme == 'http' and 
            parsed_full.netloc == parsed_base.netloc and
            not href.strip().startswith('//')):
            full_url = full_url.replace('http://', 'https://', 1)

    # Use proper URL parsing
    parsed = urlparse(full_url)

    # Only perform the most critical normalizations
    # 1. Lowercase hostname
    # 2. Remove fragment
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc.lower(),
        parsed.path or '/',  # Preserve trailing slash
        parsed.params,
        parsed.query,
        ''  # Remove fragment
    ))

    return normalized