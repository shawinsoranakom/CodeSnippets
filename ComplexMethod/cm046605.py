def _normalize_image_context_value(value: Any, *, base_path: str | None = None) -> Any:
    if isinstance(value, str):
        return value

    if isinstance(value, (bytes, bytearray)):
        return _encode_bytes_to_base64(value)

    pil_base64 = _pil_image_to_base64(value)
    if pil_base64 is not None:
        return pil_base64

    if isinstance(value, dict):
        url = value.get("url")
        if isinstance(url, str):
            return url

        image_url = value.get("image_url")
        if isinstance(image_url, str):
            return image_url
        if isinstance(image_url, dict):
            nested_url = image_url.get("url")
            if isinstance(nested_url, str):
                return nested_url

        inline_data = value.get("data")
        if isinstance(inline_data, str):
            return inline_data

        raw_bytes = value.get("bytes")
        if isinstance(raw_bytes, (bytes, bytearray)):
            return _encode_bytes_to_base64(raw_bytes)
        if isinstance(raw_bytes, str) and raw_bytes.strip():
            return raw_bytes

        path_value = value.get("path")
        if isinstance(path_value, str) and path_value.strip():
            if as_base64 := _load_image_file_to_base64(path_value, base_path = base_path):
                return as_base64
            return path_value

    return value