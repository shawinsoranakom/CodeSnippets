async def upload_unstructured_file(
    file: UploadFile = FastAPIFile(...),
    block_id: str = Form(...),
    existing_file_ids: str = Form(""),
) -> UnstructuredFileUploadResponse:
    _validate_safe_id(block_id, "block_id")

    tracked_ids = [fid.strip() for fid in existing_file_ids.split(",") if fid.strip()]

    original_filename = file.filename or "upload"
    ext = Path(original_filename).suffix.lower()
    if ext not in UNSTRUCTURED_ALLOWED_EXTS:
        raise HTTPException(
            400,
            f"Unsupported file type: {ext}. Allowed: {', '.join(sorted(UNSTRUCTURED_ALLOWED_EXTS))}",
        )

    content = await file.read()
    size_bytes = len(content)

    if size_bytes == 0:
        raise HTTPException(400, "Empty file not allowed")

    if size_bytes > MAX_FILE_SIZE:
        raise HTTPException(
            413, f"File too large ({size_bytes} bytes). Maximum is 50MB."
        )

    block_dir = UNSTRUCTURED_UPLOAD_ROOT / block_id
    ensure_dir(block_dir)
    current_total = _get_block_total_size(block_dir, file_ids = tracked_ids)
    if current_total + size_bytes > MAX_TOTAL_SIZE:
        raise HTTPException(
            413, f"Total upload limit ({MAX_TOTAL_SIZE // (1024 * 1024)}MB) exceeded"
        )

    file_id = uuid4().hex
    raw_path = block_dir / f"{file_id}{ext}"
    raw_path.write_bytes(content)

    extracted_path = block_dir / f"{file_id}.extracted.txt"
    try:
        extracted_text = _extract_text_from_file(raw_path, ext)
        if not extracted_text or not extracted_text.strip():
            raw_path.unlink(missing_ok = True)
            return UnstructuredFileUploadResponse(
                file_id = file_id,
                filename = original_filename,
                size_bytes = size_bytes,
                status = "error",
                error = "No extractable text found in file",
            )
        extracted_path.write_text(extracted_text, encoding = "utf-8")
    except Exception as e:
        raw_path.unlink(missing_ok = True)
        extracted_path.unlink(missing_ok = True)
        return UnstructuredFileUploadResponse(
            file_id = file_id,
            filename = original_filename,
            size_bytes = size_bytes,
            status = "error",
            error = f"Text extraction failed: {type(e).__name__}: {e}",
        )

    try:
        meta_path = block_dir / f"{file_id}.meta.json"
        meta_path.write_text(
            json.dumps(
                {"original_filename": original_filename, "size_bytes": size_bytes}
            ),
            encoding = "utf-8",
        )
    except OSError:
        raw_path.unlink(missing_ok = True)
        extracted_path.unlink(missing_ok = True)
        return UnstructuredFileUploadResponse(
            file_id = file_id,
            filename = original_filename,
            size_bytes = size_bytes,
            status = "error",
            error = "Failed to save file metadata",
        )

    return UnstructuredFileUploadResponse(
        file_id = file_id,
        filename = original_filename,
        size_bytes = size_bytes,
        status = "ok",
    )