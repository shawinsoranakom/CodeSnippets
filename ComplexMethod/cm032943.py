def _clean_headers(
    headers: Optional[Dict[str, str]], auth_token: Optional[str] = None
) -> Optional[Dict[str, str]]:
    merged_headers: Dict[str, str] = {}
    if DEFAULT_USER_AGENT:
        merged_headers["User-Agent"] = DEFAULT_USER_AGENT
    if auth_token:
        merged_headers["Authorization"] = auth_token
    if headers is None:
        return merged_headers or None
    merged_headers.update({str(k): str(v) for k, v in headers.items() if v is not None})
    return merged_headers or None