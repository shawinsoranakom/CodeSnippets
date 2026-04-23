async def upload_skill(file: UploadFile = File(...)):
    """Accept zip file or multiple files, extract, return file list + parsed SKILL.md metadata"""
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are accepted")
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail=f"Upload exceeds {MAX_UPLOAD_SIZE // (1024*1024)}MB limit")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            skill_files = {}
            file_list = []
            for name in zf.namelist():
                if name.endswith("/") or name.startswith("__MACOSX") or "/.DS_Store" in name or name.endswith(".DS_Store"):
                    continue
                if not _is_safe_path(name):
                    logger.warning(f"Skipping unsafe zip entry: {name}")
                    continue
                if not _is_allowed_file(name):
                    logger.info(f"Skipping non-text file: {name}")
                    continue
                raw = zf.read(name)
                if len(raw) > MAX_FILE_SIZE:
                    logger.warning(f"Skipping oversized file: {name} ({len(raw)} bytes)")
                    continue
                if len(file_list) >= MAX_FILE_COUNT:
                    logger.warning("Max file count reached, skipping remaining entries")
                    break
                file_content = raw.decode("utf-8", errors="ignore")
                skill_files[name] = file_content
                file_list.append(name)

            # Normalize paths: strip common prefix directory
            if file_list:
                common = os.path.commonpath(file_list)
                if common and common != file_list[0]:
                    skill_files = {os.path.relpath(k, common): v for k, v in skill_files.items()}
                    file_list = [os.path.relpath(f, common) for f in file_list]

            return create_session_from_files(skill_files, file_list)
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid zip file")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Error processing file")