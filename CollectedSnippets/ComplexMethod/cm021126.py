def _normalize_diagnostics(data: Any, parent_key: str | None = None) -> Any:
    """Normalize diagnostics data for deterministic snapshots.

    Removes repr fields (contain memory addresses), redacts sensitive keys,
    and normalizes hex IDs, MAC addresses, IP addresses, UUIDs, emails, and
    anonymized names that may be randomly generated.
    """
    if isinstance(data, dict):
        return {
            k: _normalize_diagnostics(v, k)
            for k, v in data.items()
            if k != "repr"  # Remove repr fields with memory addresses
        }
    if isinstance(data, list):
        return [_normalize_diagnostics(item) for item in data]
    if isinstance(data, str):
        # Redact sensitive keys
        if parent_key in REDACT_KEYS:
            return "**REDACTED**"
        # Always redact certain keys regardless of pattern
        if parent_key in ALWAYS_REDACT_KEYS:
            return "**REDACTED_NAME**"
        # Normalize anonymized names (pattern-matched)
        if parent_key in NAME_KEYS and ANON_NAME_PATTERN.match(data):
            return "**REDACTED_NAME**"
        if HEX_ID_PATTERN.match(data):
            return "**REDACTED_ID**"
        if MAC_PATTERN.match(data):
            return "**REDACTED_MAC**"
        if IPV4_PATTERN.match(data):
            return "**REDACTED_IP**"
        if UUID_PATTERN.match(data):
            return "**REDACTED_UUID**"
        if EMAIL_PATTERN.match(data):
            return "**REDACTED**@example.com"
        # Normalize permission strings with embedded IDs
        if match := PERMISSION_ID_PATTERN.match(data):
            return f"{match.group(1)}**REDACTED_ID**"
    return data