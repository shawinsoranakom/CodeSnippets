def _is_image_value(value) -> bool:
    """Check if a single sample value looks like image data."""
    if value is None:
        return False

    # PIL Image instance
    try:
        from PIL.Image import Image as PILImage

        if isinstance(value, PILImage):
            return True
    except ImportError:
        pass

    # HF datasets Image feature stores decoded images as PIL or dicts with
    # {"bytes": b"...", "path": "..."} when not yet decoded.
    # Exclude audio dicts (decoded audio has "array" + "sampling_rate").
    if isinstance(value, dict):
        if "array" in value and "sampling_rate" in value:
            return False  # This is audio, not image
        if "bytes" in value and "path" in value:
            # Check path extension to exclude audio files
            path = value.get("path") or ""
            if isinstance(path, str) and any(
                path.lower().endswith(ext) for ext in _AUDIO_EXTENSIONS
            ):
                return False
            return True

    # Raw bytes with a known image magic header
    if isinstance(value, (bytes, bytearray)):
        return _has_image_header(value)

    # String that looks like an image file path or URL
    _IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".svg")
    if isinstance(value, str) and len(value) < 1000:
        lower = value.strip().lower()
        # Image URL (http://... ending in image extension)
        if lower.startswith(("http://", "https://")) and any(
            lower.split("?")[0].endswith(ext) for ext in _IMAGE_EXTS
        ):
            return True
        # Image file path (relative or absolute path ending in image extension)
        if any(lower.endswith(ext) for ext in _IMAGE_EXTS):
            return True

    return False