def _to_pil_from_hf_image_dict(value: Any) -> Any | None:
    if not isinstance(value, dict):
        return None

    raw_bytes = value.get("bytes")
    if isinstance(raw_bytes, (bytes, bytearray)) and len(raw_bytes) > 0:
        try:
            return _open_pil_image_from_bytes(bytes(raw_bytes))
        except (OSError, ValueError):
            pass
    if (
        isinstance(raw_bytes, list)
        and len(raw_bytes) > 0
        and all(isinstance(item, int) and 0 <= item <= 255 for item in raw_bytes)
    ):
        try:
            return _open_pil_image_from_bytes(bytes(raw_bytes))
        except (OSError, ValueError):
            pass

    path_value = value.get("path")
    if isinstance(path_value, str) and path_value.strip():
        try:
            from PIL import Image  # type: ignore

            with Image.open(Path(path_value)) as image:
                return image.copy()
        except (OSError, ValueError, TypeError):
            return None

    return None