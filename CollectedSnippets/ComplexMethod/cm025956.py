def should_compress(content_type: str, path: str | None = None) -> bool:
    """Return if we should compress a response."""
    if path is not None and NO_COMPRESS.match(path):
        return False
    if content_type.startswith("text/event-stream"):
        return False
    if content_type.startswith("image/"):
        return "svg" in content_type
    if content_type.startswith("application/"):
        return (
            "json" in content_type
            or "xml" in content_type
            or "javascript" in content_type
        )
    return not content_type.startswith(("video/", "audio/", "font/"))