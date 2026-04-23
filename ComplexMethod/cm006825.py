def validate_headers(headers: dict[str, str]) -> dict[str, str]:
    """Validate and sanitize HTTP headers according to RFC 7230.

    Args:
        headers: Dictionary of header name-value pairs

    Returns:
        Dictionary of validated and sanitized headers

    Raises:
        ValueError: If headers contain invalid names or values
    """
    if not headers:
        return {}

    sanitized_headers = {}

    for name, value in headers.items():
        if not isinstance(name, str) or not isinstance(value, str):
            logger.warning(f"Skipping non-string header: {name}={value}")
            continue

        # Validate header name according to RFC 7230
        if not HEADER_NAME_PATTERN.match(name):
            logger.warning(f"Invalid header name '{name}', skipping")
            continue

        # Normalize header name to lowercase (HTTP headers are case-insensitive)
        normalized_name = name.lower()

        # Optional: Check against whitelist of allowed headers
        if normalized_name not in ALLOWED_HEADERS:
            # For MCP, we'll be permissive and allow non-standard headers
            # but log a warning for security awareness
            logger.debug(f"Using non-standard header: {normalized_name}")

        # Check for potential header injection attempts BEFORE sanitizing
        if "\r" in value or "\n" in value:
            logger.warning(f"Potential header injection detected in '{name}', skipping")
            continue

        # Sanitize header value - remove control characters and newlines
        # RFC 7230: field-value = *( field-content / obs-fold )
        # We'll remove control characters (0x00-0x1F, 0x7F) except tab (0x09) and space (0x20)
        sanitized_value = re.sub(r"[\x00-\x08\x0A-\x1F\x7F]", "", value)

        # Remove leading/trailing whitespace
        sanitized_value = sanitized_value.strip()

        if not sanitized_value:
            logger.warning(f"Header '{name}' has empty value after sanitization, skipping")
            continue

        sanitized_headers[normalized_name] = sanitized_value

    return sanitized_headers