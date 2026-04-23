def to_preview_jsonable(value: Any) -> Any:
    """Convert values into JSON-safe preview values, including PIL images."""
    image_payload = _to_preview_image_payload(value)
    if image_payload is not None:
        return image_payload

    converted = to_jsonable(value)
    if converted is None or isinstance(converted, (str, int, float, bool)):
        return converted
    if isinstance(converted, dict):
        return {str(k): to_preview_jsonable(v) for k, v in converted.items()}
    if isinstance(converted, (list, tuple, set)):
        return [to_preview_jsonable(v) for v in converted]
    if isinstance(converted, (bytes, bytearray)):
        return base64.b64encode(bytes(converted)).decode("ascii")
    return str(converted)