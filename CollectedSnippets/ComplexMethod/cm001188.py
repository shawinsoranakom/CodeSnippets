def _validate_checkout_redirect_url(url: str) -> bool:
    """Return True if `url` matches the configured frontend origin.

    Prevents open-redirect: attackers must not be able to supply arbitrary
    success_url/cancel_url that Stripe will redirect users to after checkout.

    Pre-parse rejection rules (applied before urlparse):
    - Backslashes (``\\``) are normalised differently across parsers/browsers.
    - Control characters (U+0000–U+001F) are not valid in URLs and may confuse
      some URL-parsing implementations.
    """
    # Reject characters that can confuse URL parsers before any parsing.
    if "\\" in url:
        return False
    if any(ord(c) < 0x20 for c in url):
        return False

    allowed = settings.config.frontend_base_url or settings.config.platform_base_url
    if not allowed:
        # No configured origin — refuse to validate rather than allow arbitrary URLs.
        return False
    try:
        parsed = urlparse(url)
        allowed_parsed = urlparse(allowed)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    # Reject ``user:pass@host`` authority tricks — ``@`` in the netloc component
    # can trick browsers into connecting to a different host than displayed.
    # ``@`` in query/fragment is harmless and must be allowed.
    if "@" in parsed.netloc:
        return False
    return (
        parsed.scheme == allowed_parsed.scheme
        and parsed.netloc == allowed_parsed.netloc
    )