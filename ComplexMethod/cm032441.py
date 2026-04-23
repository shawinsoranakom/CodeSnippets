def _api_post_json(url: str, payload: dict, timeout_s: int = 10) -> tuple[int, dict | None]:
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
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
        raise RuntimeError(f"HTTPError {exc.code}: {parsed or body!r}") from exc
    except URLError as exc:
        raise RuntimeError(f"URLError: {exc}") from exc