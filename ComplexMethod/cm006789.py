def detect_image_type_from_bytes(content: bytes) -> str | None:
    """Detect the actual image type from file content using magic bytes.

    Args:
        content: The file content bytes (at least first 12 bytes needed)

    Returns:
        str | None: The detected image type (e.g., "jpeg", "png") or None if not recognized
    """
    if len(content) < MIN_IMAGE_HEADER_SIZE:
        return None

    # Check WebP specifically (needs to check both RIFF and WEBP)
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"

    # Check other image signatures
    for image_type, signatures in IMAGE_SIGNATURES.items():
        if image_type == "webp":
            continue  # Already handled above
        for signature, offset in signatures:
            if content[offset : offset + len(signature)] == signature:
                return image_type

    return None