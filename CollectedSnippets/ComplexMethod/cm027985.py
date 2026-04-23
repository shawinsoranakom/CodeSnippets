async def upload_files(files: List[UploadFile] = File(...)):
    """Accept multiple files (folder upload via webkitdirectory)"""
    if len(files) > MAX_FILE_COUNT:
        raise HTTPException(status_code=413, detail=f"Too many files (max {MAX_FILE_COUNT})")
    skill_files = {}
    file_list = []
    total_size = 0
    for f in files:
        if f.filename.startswith(".") or "/.DS_Store" in (f.filename or "") or "__MACOSX" in (f.filename or ""):
            continue
        name = f.filename or "unknown"
        if not _is_safe_path(name):
            logger.warning(f"Skipping unsafe path: {name}")
            continue
        if not _is_allowed_file(name):
            logger.info(f"Skipping non-text file: {name}")
            continue
        content = await f.read()
        total_size += len(content)
        if total_size > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail=f"Total upload exceeds {MAX_UPLOAD_SIZE // (1024*1024)}MB limit")
        if len(content) > MAX_FILE_SIZE:
            logger.warning(f"Skipping oversized file: {name} ({len(content)} bytes)")
            continue
        skill_files[name] = content.decode("utf-8", errors="ignore")
        file_list.append(name)

    # Normalize paths: strip common prefix directory
    if file_list:
        common = os.path.commonpath(file_list)
        if common and common != file_list[0]:
            skill_files = {os.path.relpath(k, common): v for k, v in skill_files.items()}
            file_list = [os.path.relpath(f, common) for f in file_list]

    return create_session_from_files(skill_files, file_list)