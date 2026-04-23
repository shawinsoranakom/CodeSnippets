def _download_file_blob(
    service: GoogleDriveService,
    file: GoogleDriveFileType,
    size_threshold: int,
    allow_images: bool,
) -> tuple[bytes, str] | None:
    mime_type = file.get("mimeType", "")
    file_id = file.get("id")
    if not file_id:
        logging.warning("Encountered Google Drive file without id.")
        return None

    if is_gdrive_image_mime_type(mime_type) and not allow_images:
        logging.debug(f"Skipping image {file.get('name')} because allow_images is False.")
        return None

    blob: bytes = b""
    extension = ".bin"
    try:
        if mime_type in GOOGLE_NATIVE_EXPORT_TARGETS:
            export_mime, extension = GOOGLE_NATIVE_EXPORT_TARGETS[mime_type]
            request = service.files().export_media(fileId=file_id, mimeType=export_mime)
            blob = _download_request(request, file_id, size_threshold)
        elif mime_type.startswith("application/vnd.google-apps"):
            export_mime, extension = GOOGLE_NATIVE_EXPORT_FALLBACK
            request = service.files().export_media(fileId=file_id, mimeType=export_mime)
            blob = _download_request(request, file_id, size_threshold)
        else:
            extension = _get_extension_from_file(file, mime_type)
            blob = download_request(service, file_id, size_threshold)
    except HttpError:
        raise

    if not blob:
        return None
    if not extension:
        extension = _get_extension_from_file(file, mime_type)
    return blob, extension