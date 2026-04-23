def _extract_token_from_headers(headers: Any) -> str | None:
    if not headers or not hasattr(headers, "get"):
        return None

    auth_keys = ("authorization", "Authorization", b"authorization", b"Authorization")
    for key in auth_keys:
        auth = headers.get(key)
        if not auth:
            continue
        auth_text = _to_text(auth).strip()
        if auth_text.lower().startswith("bearer "):
            token = auth_text[7:].strip()
            if token:
                return token

    api_key_keys = ("api_key", "x-api-key", "Api-Key", "X-API-Key", b"api_key", b"x-api-key", b"Api-Key", b"X-API-Key")
    for key in api_key_keys:
        token = headers.get(key)
        if token:
            token_text = _to_text(token).strip()
            if token_text:
                return token_text

    return None