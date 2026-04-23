def _api_request_json(
    url: str,
    method: str = "GET",
    payload: dict | None = None,
    headers: dict | None = None,
    timeout_s: int = 10,
) -> tuple[int, dict | None]:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = Request(url, data=data, headers=req_headers, method=method)
    try:
        with urlopen(req, timeout=timeout_s) as resp:
            body = resp.read()
            if body:
                try:
                    return resp.status, json.loads(body.decode("utf-8"))
                except Exception:
                    return resp.status, None
            return resp.status, None
    except HTTPError as exc:
        body = exc.read()
        parsed = None
        if body:
            try:
                parsed = json.loads(body.decode("utf-8"))
            except Exception:
                parsed = None
        raise RuntimeError(
            f"{method} {url} failed with HTTPError {exc.code}: {parsed or body!r}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"{method} {url} failed with URLError: {exc}") from exc