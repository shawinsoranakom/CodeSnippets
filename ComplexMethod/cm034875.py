def _make_api_request(
    api_url: str, token: str, params: dict[str, Any]
) -> dict[str, Any]:
    """
    Make PaddleOCR API request.

    Args:
        api_url: API endpoint URL
        token: Access token
        params: Request parameters

    Returns:
        API response dict

    Raises:
        RuntimeError: On API errors
    """
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json",
        "Client-Platform": "official-skill",
    }

    timeout = _http_timeout_from_env("PADDLEOCR_OCR_TIMEOUT", float(DEFAULT_TIMEOUT))

    try:
        with httpx.Client(timeout=timeout) as client:
            try:
                resp = client.post(api_url, json=params, headers=headers)
            except TypeError as e:
                raise RuntimeError(
                    "Request parameters cannot be JSON-encoded; use only JSON-serializable "
                    f"option values ({e})"
                ) from e
    except httpx.TimeoutException:
        raise RuntimeError(f"API request timed out after {timeout}s")
    except httpx.RequestError as e:
        raise RuntimeError(f"API request failed: {e}")

    if resp.status_code != 200:
        error_detail = ""
        try:
            error_body = resp.json()
            if isinstance(error_body, dict):
                error_detail = str(error_body.get("errorMsg", "")).strip()
        except Exception:
            pass

        if not error_detail:
            error_detail = (resp.text[:200] or "No response body").strip()

        if resp.status_code == 403:
            raise RuntimeError(f"Authentication failed (403): {error_detail}")
        elif resp.status_code == 429:
            raise RuntimeError(f"API rate limit exceeded (429): {error_detail}")
        elif resp.status_code >= 500:
            raise RuntimeError(
                f"API service error ({resp.status_code}): {error_detail}"
            )
        else:
            raise RuntimeError(f"API error ({resp.status_code}): {error_detail}")

    try:
        result = resp.json()
    except Exception:
        raise RuntimeError(f"Invalid JSON response: {resp.text[:200]}")

    if not isinstance(result, dict):
        raise RuntimeError(
            f"Unexpected JSON shape (expected object): {resp.text[:200]}"
        )

    if result.get("errorCode", 0) != 0:
        msg = result.get("errorMsg", "Unknown error")
        raise RuntimeError(f"API error: {msg}")

    return result