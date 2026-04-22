def _make_blocking_http_get(url: str, timeout: float = 5) -> Optional[str]:
    try:
        text = requests.get(url, timeout=timeout).text
        if isinstance(text, str):
            text = text.strip()
        return text
    except Exception:
        return None