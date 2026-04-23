def _convert_drive_item_to_document(
    creds: Any,
    allow_images: bool,
    size_threshold: int,
    retriever_email: str,
    file: GoogleDriveFileType,
    # if not specified, we will not sync permissions
    # will also be a no-op if EE is not enabled
    permission_sync_context: PermissionSyncContext | None,
) -> Document | ConnectorFailure | None:
    """
    Main entry point for converting a Google Drive file => Document object.
    """

    def _get_drive_service() -> GoogleDriveService:
        return get_drive_service(creds, user_email=retriever_email)

    doc_id = "unknown"
    link = file.get(WEB_VIEW_LINK_KEY)

    try:
        if file.get("mimeType") in [DRIVE_SHORTCUT_TYPE, DRIVE_FOLDER_TYPE]:
            logging.info("Skipping shortcut/folder.")
            return None

        size_str = file.get("size")
        if size_str:
            try:
                size_int = int(size_str)
            except ValueError:
                logging.warning(f"Parsing string to int failed: size_str={size_str}")
            else:
                if size_int > size_threshold:
                    logging.warning(f"{file.get('name')} exceeds size threshold of {size_threshold}. Skipping.")
                    return None

        blob_and_ext = _download_file_blob(
            service=_get_drive_service(),
            file=file,
            size_threshold=size_threshold,
            allow_images=allow_images,
        )

        if blob_and_ext is None:
            logging.info(f"Skipping file {file.get('name')} due to incompatible type or download failure.")
            return None

        blob, extension = blob_and_ext
        if not blob:
            logging.warning(f"Failed to download {file.get('name')}. Skipping.")
            return None

        doc_id = onyx_document_id_from_drive_file(file)
        modified_time = file.get("modifiedTime")
        try:
            doc_updated_at = datetime.fromisoformat(modified_time.replace("Z", "+00:00")) if modified_time else datetime.now(timezone.utc)
        except ValueError:
            logging.warning(f"Failed to parse modifiedTime for {file.get('name')}, defaulting to current time.")
            doc_updated_at = datetime.now(timezone.utc)

        return Document(
            id=doc_id,
            source=DocumentSource.GOOGLE_DRIVE,
            semantic_identifier=file.get("name", ""),
            blob=blob,
            extension=extension,
            size_bytes=len(blob),
            doc_updated_at=doc_updated_at,
        )
    except Exception as e:
        doc_id = "unknown"
        try:
            doc_id = onyx_document_id_from_drive_file(file)
        except Exception as e2:
            logging.warning(f"Error getting document id from file: {e2}")

        file_name = file.get("name", doc_id)
        error_str = f"Error converting file '{file_name}' to Document as {retriever_email}: {e}"
        if isinstance(e, HttpError) and e.status_code == 403:
            logging.warning(f"Uncommon permissions error while downloading file. User {retriever_email} was able to see file {file_name} but cannot download it.")
            logging.warning(error_str)

        return ConnectorFailure(
            failed_document=DocumentFailure(
                document_id=doc_id,
                document_link=link,
            ),
            failed_entity=None,
            failure_message=error_str,
            exception=e,
        )