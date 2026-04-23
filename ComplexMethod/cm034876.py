def ocr(
    file_path: Optional[str] = None,
    file_url: Optional[str] = None,
    file_type: Optional[int] = None,
    **options: Any,
) -> dict[str, Any]:
    """
    Perform OCR on image or PDF.

    Args:
        file_path: Local file path (mutually exclusive with file_url)
        file_url: URL to file (mutually exclusive with file_path)
        file_type: Optional file type override (0=PDF, 1=Image)
        **options: Additional API options (passed directly to API)

    Returns:
        {
            "ok": True,
            "text": "extracted text...",
            "result": { raw API result },
            "error": None
        }
        or on error:
        {
            "ok": False,
            "text": "",
            "result": None,
            "error": {"code": "...", "message": "..."}
        }
    """
    if file_path is not None and not isinstance(file_path, str):
        return _error("INPUT_ERROR", "file_path must be a string or None")
    if file_url is not None and not isinstance(file_url, str):
        return _error("INPUT_ERROR", "file_url must be a string or None")

    fp = file_path.strip() if file_path else ""
    fu = file_url.strip() if file_url else ""
    if fp and fu:
        return _error(
            "INPUT_ERROR",
            "Provide only one of file_path or file_url, not both",
        )
    if not fp and not fu:
        return _error("INPUT_ERROR", "file_path or file_url required")
    if file_type is not None and file_type not in (FILE_TYPE_PDF, FILE_TYPE_IMAGE):
        return _error("INPUT_ERROR", "file_type must be 0 (PDF) or 1 (Image)")

    try:
        api_url, token = get_config()
    except ValueError as e:
        return _error("CONFIG_ERROR", str(e))

    # Build request params
    try:
        resolved_file_type: Optional[int] = None
        if fu:
            params = {"file": fu}
            if file_type is not None:
                resolved_file_type = file_type
            else:
                try:
                    resolved_file_type = _detect_file_type(fu)
                except ValueError:
                    resolved_file_type = None
        else:
            resolved_file_type = (
                file_type if file_type is not None else _detect_file_type(fp)
            )
            params = {"file": _load_file_as_base64(fp)}

        params["visualize"] = (
            False  # reduce response payload; callers can override via options
        )
        params.update(options)
        if resolved_file_type is not None:
            params["fileType"] = resolved_file_type
        else:
            params.pop("fileType", None)

    except (ValueError, OSError, MemoryError) as e:
        return _error("INPUT_ERROR", str(e))

    try:
        result = _make_api_request(api_url, token, params)
    except RuntimeError as e:
        return _error("API_ERROR", str(e))

    try:
        text = _extract_text(result)
    except ValueError as e:
        return _error("API_ERROR", str(e))

    return {
        "ok": True,
        "text": text,
        "result": result,
        "error": None,
    }