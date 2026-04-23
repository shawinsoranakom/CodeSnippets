def inspect_seed_upload(payload: SeedInspectUploadRequest) -> SeedInspectResponse:
    if payload.file_ids is not None:
        if len(payload.file_ids) == 0:
            raise HTTPException(400, "file_ids must not be empty")
        _validate_safe_id(payload.block_id, "block_id")
        for fid in payload.file_ids:
            _validate_safe_id(fid, "file_id")
        preview_rows = _read_preview_rows_from_multi_files(
            block_id = payload.block_id,
            file_ids = payload.file_ids,
            file_names = payload.file_names,
            preview_size = payload.preview_size,
            chunk_size = payload.unstructured_chunk_size,
            chunk_overlap = payload.unstructured_chunk_overlap,
        )
        columns = ["chunk_text", "source_file"] if preview_rows else []
        resolved_paths = [
            str(UNSTRUCTURED_UPLOAD_ROOT / payload.block_id / f"{fid}.extracted.txt")
            for fid in payload.file_ids
        ]
        return SeedInspectResponse(
            dataset_name = "unstructured_seed",
            resolved_path = resolved_paths[0] if resolved_paths else "",
            resolved_paths = resolved_paths,
            columns = columns,
            preview_rows = _serialize_preview_rows(preview_rows),
        )

    seed_source_type = _normalize_optional_text(payload.seed_source_type) or "local"
    filename = _sanitize_filename(payload.filename)
    ext = Path(filename).suffix.lower()
    # Legacy single-file unstructured path only supports .txt/.md
    # PDF/DOCX extraction uses the multi-file upload endpoint instead
    _LEGACY_UNSTRUCTURED_EXTS = {".txt", ".md"}
    if seed_source_type == "unstructured":
        if ext not in _LEGACY_UNSTRUCTURED_EXTS:
            allowed = ", ".join(sorted(_LEGACY_UNSTRUCTURED_EXTS))
            raise HTTPException(
                status_code = 400,
                detail = f"unsupported file type: {ext}. allowed: {allowed}",
            )
    else:
        if ext not in LOCAL_UPLOAD_EXTS:
            allowed = ", ".join(sorted(LOCAL_UPLOAD_EXTS))
            raise HTTPException(
                status_code = 400,
                detail = f"unsupported file type: {ext}. allowed: {allowed}",
            )

    file_bytes = _decode_base64_payload(payload.content_base64)
    if not file_bytes:
        raise HTTPException(status_code = 400, detail = "empty upload payload")
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code = 413, detail = "file too large (max 50MB)")

    ensure_dir(SEED_UPLOAD_DIR)
    stored_name = f"{uuid4().hex}_{filename}"
    stored_path = SEED_UPLOAD_DIR / stored_name
    stored_path.write_bytes(file_bytes)

    if seed_source_type == "unstructured":
        preview_rows = _read_preview_rows_from_unstructured_file(
            path = stored_path,
            preview_size = int(payload.preview_size),
            chunk_size = payload.unstructured_chunk_size,
            chunk_overlap = payload.unstructured_chunk_overlap,
        )
    else:
        preview_rows = _read_preview_rows_from_local_file(
            stored_path,
            int(payload.preview_size),
        )
    if not preview_rows:
        raise HTTPException(
            status_code = 422, detail = "dataset appears empty or unreadable"
        )
    columns = _extract_columns(preview_rows)

    return SeedInspectResponse(
        dataset_name = filename,
        resolved_path = str(stored_path),
        columns = columns,
        preview_rows = preview_rows,
        split = None,
        subset = None,
    )