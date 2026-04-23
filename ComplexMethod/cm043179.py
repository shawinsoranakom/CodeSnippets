def normalize_url(
    href: str,
    base_url: str,
    *,
    drop_query_tracking=True,
    sort_query=True,
    keep_fragment=False,
    extra_drop_params=None,
    preserve_https=False,
    original_scheme=None
):
    """
    Extended URL normalizer

    Parameters
    ----------
    href : str
        The raw link extracted from a page.
    base_url : str
        The page’s canonical URL (used to resolve relative links).
    drop_query_tracking : bool (default True)
        Remove common tracking query parameters.
    sort_query : bool (default True)
        Alphabetically sort query keys for deterministic output.
    keep_fragment : bool (default False)
        Preserve the hash fragment (#section) if you need in-page links.
    extra_drop_params : Iterable[str] | None
        Additional query keys to strip (case-insensitive).

    Returns
    -------
    str | None
        A clean, canonical URL or None if href is empty/None.
    """
    if not href:
        return None

    # Resolve relative paths first
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

    # Parse once, edit parts, then rebuild
    parsed = urlparse(full_url)

    # ── netloc ──
    netloc = parsed.netloc.lower()

    # ── path ──
    # Strip duplicate slashes and trailing "/" (except root)
    # IMPORTANT: Don't use quote(unquote()) as it mangles + signs in URLs
    # The path from urlparse is already properly encoded
    path = parsed.path
    # Preserve trailing slashes -- they are semantically significant per RFC 3986
    # e.g. /page/9123/ and /page/9123 may return different responses

    # ── query ──
    query = parsed.query
    if query:
        # explode, mutate, then rebuild
        params = [(k, v) for k, v in parse_qsl(query, keep_blank_values=True)]

        if drop_query_tracking:
            default_tracking = {
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term',
                'utm_content', 'gclid', 'fbclid', 'ref', 'ref_src'
            }
            if extra_drop_params:
                default_tracking |= {p.lower() for p in extra_drop_params}
            params = [(k, v) for k, v in params if k.lower() not in default_tracking]

        if sort_query:
            params.sort(key=lambda kv: kv[0])

        query = urlencode(params, doseq=True) if params else ''

    # ── fragment ──
    fragment = parsed.fragment if keep_fragment else ''

    # Re-assemble
    normalized = urlunparse((
        parsed.scheme,
        netloc,
        path,
        parsed.params,
        query,
        fragment
    ))

    return normalized