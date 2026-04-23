async def stage_multipart_request(request: Request) -> MultipartPayload:
    temp_dir = tempfile.mkdtemp(prefix="mineru-router-request-")
    uploads: list[StagedUpload] = []
    fields: list[tuple[str, str]] = []

    try:
        form = await request.form()
        for key, value in form.multi_items():
            if isinstance(value, StarletteUploadFile):
                original_name = value.filename or f"upload-{uuid.uuid4()}"
                filename = normalize_upload_filename(original_name)
                destination = build_upload_destination(temp_dir, filename)
                with open(destination, "wb") as handle:
                    while True:
                        chunk = await value.read(1 << 20)
                        if not chunk:
                            break
                        handle.write(chunk)
                uploads.append(
                    StagedUpload(
                        field_name=key,
                        upload_name=original_name,
                        content_type=value.content_type or "application/octet-stream",
                        path=str(destination),
                    )
                )
                await value.close()
            else:
                fields.append((key, str(value)))
    except Exception:
        cleanup_path(temp_dir)
        raise

    return MultipartPayload(temp_dir=temp_dir, fields=fields, uploads=uploads)