def _has_image_header(data: bytes) -> bool:
    """Quick magic-byte check for common image formats."""
    if len(data) < 4:
        return False
    # JPEG
    if data[:2] == b"\xff\xd8":
        return True
    # PNG
    if data[:4] == b"\x89PNG":
        return True
    # GIF
    if data[:3] == b"GIF":
        return True
    # WebP
    if data[:4] == b"RIFF" and len(data) >= 12 and data[8:12] == b"WEBP":
        return True
    # BMP
    if data[:2] == b"BM":
        return True
    return False