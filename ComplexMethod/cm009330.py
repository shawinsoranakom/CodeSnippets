def parse_url_with_auth(
    url: str | None,
) -> tuple[str | None, dict[str, str] | None]:
    """Parse URL and extract `userinfo` credentials for headers.

    Handles URLs of the form: `https://user:password@host:port/path`

    Scheme-less URLs (e.g., `host:port`) are also accepted and will be
    given a default `http://` scheme.

    Args:
        url: The URL to parse.

    Returns:
        A tuple of `(cleaned_url, headers_dict)` where:
        - `cleaned_url` is a normalized URL with credentials stripped (if any
            were present) and a scheme guaranteed (defaulting to `http://` for
            scheme-less inputs). Returns the original URL unchanged when it
            already has a valid scheme and no credentials.
        - `headers_dict` contains Authorization header if credentials were found.
    """
    if not url:
        return None, None

    parsed = urlparse(url)
    needs_reconstruction = False
    valid = False

    if parsed.scheme in {"http", "https"} and parsed.netloc and parsed.hostname:
        valid = True
    elif not (parsed.scheme and parsed.netloc) and ":" in url:
        # No valid scheme but contains colon — try as scheme-less host:port
        parsed_with_scheme = urlparse(f"http://{url}")
        if parsed_with_scheme.netloc and parsed_with_scheme.hostname:
            parsed = parsed_with_scheme
            needs_reconstruction = True
            valid = True

    # Validate port is numeric (urlparse raises ValueError for non-numeric ports)
    if valid:
        try:
            _ = parsed.port
        except ValueError:
            valid = False

    if not valid:
        return None, None

    if not parsed.username:
        cleaned = _build_cleaned_url(parsed) if needs_reconstruction else url
        return cleaned, None

    # Handle case where password might be empty string or None
    password = parsed.password or ""

    # Create basic auth header (decode percent-encoding)
    username = unquote(parsed.username)
    password = unquote(password)
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {"Authorization": f"Basic {encoded_credentials}"}

    return _build_cleaned_url(parsed), headers