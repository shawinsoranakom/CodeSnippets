def get_request_json_payload(response) -> dict:
    payload = None
    request = response.request
    try:
        post_data_json = request.post_data_json
        payload = post_data_json() if callable(post_data_json) else post_data_json
    except Exception:
        payload = None

    if payload is None:
        try:
            post_data = request.post_data
            raw = post_data() if callable(post_data) else post_data
            if raw:
                payload = json.loads(raw)
        except Exception:
            payload = None

    if not isinstance(payload, dict):
        raise AssertionError(f"Expected JSON object payload for /v1/kb/update, got={payload!r}")
    return payload