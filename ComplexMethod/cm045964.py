async def save_upload_files(upload_dir: str, files: list[UploadFile]) -> list[StoredUpload]:
    os.makedirs(upload_dir, exist_ok=True)
    uploads: list[StoredUpload] = []

    for upload in files:
        original_name = upload.filename or f"upload-{uuid.uuid4()}"
        filename = normalize_upload_filename(original_name)
        normalized_stem = normalize_task_stem(Path(filename).stem)
        destination = build_upload_destination(upload_dir, filename)
        try:
            with open(destination, "wb") as handle:
                while True:
                    chunk = await upload.read(1 << 20)
                    if not chunk:
                        break
                    handle.write(chunk)

            file_suffix = guess_suffix_by_path(destination)
            if file_suffix not in SUPPORTED_UPLOAD_SUFFIXES:
                cleanup_file(str(destination))
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file_suffix}",
                )

            uploads.append(
                StoredUpload(
                    original_name=original_name,
                    stem=normalized_stem,
                    path=str(destination),
                )
            )
        except Exception:
            cleanup_file(str(destination))
            raise
        finally:
            await upload.close()

    normalized_stems, renamed_stems = uniquify_task_stems(
        [upload.stem for upload in uploads]
    )
    if renamed_stems:
        rename_details = ", ".join(
            f"{Path(upload.original_name).name} -> {effective_stem}"
            for upload, effective_stem in zip(uploads, normalized_stems)
            if upload.stem != effective_stem
        )
        logger.warning(
            f"Normalized duplicate upload stems within request: {rename_details}"
        )
        uploads = [
            StoredUpload(
                original_name=upload.original_name,
                stem=effective_stem,
                path=upload.path,
            )
            for upload, effective_stem in zip(uploads, normalized_stems)
        ]
    return uploads