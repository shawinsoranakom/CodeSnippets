async def _coerce_request_data() -> dict:
    """Fetch JSON body with sane defaults; fallback to form data."""
    if hasattr(request, "_cached_payload"):
        return request._cached_payload
    payload: Any = None

    body_bytes = await request.get_data()
    has_body = bool(body_bytes)
    content_type = (request.content_type or "").lower()
    is_json = content_type.startswith("application/json")

    if not has_body:
        payload = {}
    elif is_json:
        payload = await request.get_json(force=False, silent=False)
        if isinstance(payload, dict):
            payload = payload or {}
        elif isinstance(payload, str):
            raise AttributeError("'str' object has no attribute 'get'")
        else:
            raise TypeError("JSON payload must be an object.")
    else:
        form = await request.form
        payload = form.to_dict() if form else None
        if payload is None:
            raise TypeError("Request body is not a valid form payload.")

    request._cached_payload = payload
    return payload