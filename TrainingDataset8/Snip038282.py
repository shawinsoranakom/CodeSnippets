def get_hostname(url: str) -> Optional[str]:
    """Return the hostname of a URL (with or without protocol)."""
    # Just so urllib can parse the URL, make sure there's a protocol.
    # (The actual protocol doesn't matter to us)
    if "://" not in url:
        url = "http://%s" % url

    parsed = urllib.parse.urlparse(url)
    return parsed.hostname