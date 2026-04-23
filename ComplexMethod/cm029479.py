def _extract_partial_json_string(raw_text: str, key: str) -> Optional[str]:
    if not raw_text:
        return None
    token = f'"{key}"'
    idx = raw_text.find(token)
    if idx == -1:
        return None
    colon = raw_text.find(":", idx + len(token))
    if colon == -1:
        return None
    cursor = colon + 1
    while cursor < len(raw_text) and raw_text[cursor].isspace():
        cursor += 1
    if cursor >= len(raw_text) or raw_text[cursor] != '"':
        return None

    start = cursor + 1
    last_quote: Optional[int] = None
    cursor = start
    while cursor < len(raw_text):
        if raw_text[cursor] == '"':
            backslashes = 0
            back = cursor - 1
            while back >= start and raw_text[back] == "\\":
                backslashes += 1
                back -= 1
            if backslashes % 2 == 0:
                last_quote = cursor
        cursor += 1

    partial = raw_text[start:] if last_quote is None else raw_text[start:last_quote]
    partial = _strip_incomplete_escape(partial)
    if not partial:
        return ""

    try:
        return json.loads(f'"{partial}"')
    except Exception:
        return (
            partial.replace("\\n", "\n")
            .replace("\\t", "\t")
            .replace("\\r", "\r")
            .replace('\\"', '"')
            .replace("\\\\", "\\")
        )