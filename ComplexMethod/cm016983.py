def _snapshot_request_body_for_logging(
    content_type: str,
    method: str,
    data: dict[str, Any] | None,
    files: dict[str, Any] | list[tuple[str, Any]] | None,
) -> dict[str, Any] | str | None:
    if method.upper() == "GET":
        return None
    if content_type == "multipart/form-data":
        form_fields = sorted([k for k, v in (data or {}).items() if v is not None])
        file_fields: list[dict[str, str]] = []
        if files:
            file_iter = files if isinstance(files, list) else list(files.items())
            for field_name, file_obj in file_iter:
                if file_obj is None:
                    continue
                if isinstance(file_obj, tuple):
                    filename = file_obj[0]
                else:
                    filename = getattr(file_obj, "name", field_name)
                file_fields.append({"field": field_name, "filename": str(filename or "")})
        return {"_multipart": True, "form_fields": form_fields, "file_fields": file_fields}
    if content_type == "application/x-www-form-urlencoded":
        return data or {}
    return data or {}