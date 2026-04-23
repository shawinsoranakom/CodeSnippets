def parse_request_data(method: str, path: str, data=None, headers=None) -> dict:
    """Extract request data either from query string as well as request body (e.g., for POST)."""
    result = {}
    headers = headers or {}
    content_type = headers.get("Content-Type", "")

    # add query params to result
    parsed_path = urlparse(path)
    result.update(parse_qs(parsed_path.query))

    # add params from url-encoded payload
    if method in ["POST", "PUT", "PATCH"] and (not content_type or "form-" in content_type):
        # content-type could be either "application/x-www-form-urlencoded" or "multipart/form-data"
        try:
            params = parse_qs(to_str(data or ""))
            result.update(params)
        except Exception:
            pass  # probably binary / JSON / non-URL encoded payload - ignore

    # select first elements from result lists (this is assuming we are not using parameter lists!)
    result = {k: v[0] for k, v in result.items()}
    return result