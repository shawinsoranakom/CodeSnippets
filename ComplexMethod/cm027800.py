def _parse_address(address: str) -> dict[str, str]:
    """Extract house number, direction, street name, and suffix from address."""
    clean = address.split(",")[0].strip().upper()
    tokens = clean.split()
    if not tokens:
        return {}
    result: dict[str, str] = {}
    idx = 0
    if tokens[idx].isdigit() or re.match(r"^\d+\w*$", tokens[idx]):
        result["house"] = tokens[idx]
        idx += 1
    if idx < len(tokens) and _DIRECTION_RE.match(tokens[idx]):
        result["direction"] = tokens[idx].upper()
        idx += 1
    street_tokens = []
    while idx < len(tokens):
        t = tokens[idx]
        normalized = _SUFFIX_MAP.get(t, None)
        if normalized:
            result["suffix"] = normalized
            idx += 1
            break
        street_tokens.append(t)
        idx += 1
    result["street"] = " ".join(street_tokens)
    return result