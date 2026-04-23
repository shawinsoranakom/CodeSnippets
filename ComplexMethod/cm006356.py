def validate_provider_url(v: str, info: object | None = None, *, field_name: str | None = None) -> str:
    """Validate and normalize a provider URL.

    Enforces HTTPS-only, rejects embedded credentials, validates the URL
    structure, and normalises scheme + host to lowercase.

    *info* is the Pydantic ``ValidationInfo`` passed by field validators.
    When calling outside a Pydantic context, pass *field_name* directly
    instead.
    """
    field = field_name or getattr(info, "field_name", None) or "Field"
    stripped = v.strip()
    if not stripped:
        msg = f"{field} must not be empty"
        raise ValueError(msg)

    if len(stripped) > _MAX_URL_LENGTH:
        msg = f"{field} exceeds maximum length of {_MAX_URL_LENGTH}"
        raise ValueError(msg)

    parsed = urlparse(stripped)

    if parsed.scheme.lower() not in _ALLOWED_URL_SCHEMES:
        msg = f"{field} must use the https scheme"
        raise ValueError(msg)

    if parsed.username is not None or parsed.password is not None:
        msg = f"{field} must not contain user credentials"
        raise ValueError(msg)

    hostname = parsed.hostname
    if not hostname:
        msg = f"{field} must contain a valid hostname"
        raise ValueError(msg)

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((scheme, netloc, path, parsed.params, parsed.query, parsed.fragment))