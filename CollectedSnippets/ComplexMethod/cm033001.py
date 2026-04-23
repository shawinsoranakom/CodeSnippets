def process_attachment(
    confluence_client: "OnyxConfluence",
    attachment: dict[str, Any],
    parent_content_id: str | None,
    allow_images: bool,
) -> AttachmentProcessingResult:
    """
    Processes a Confluence attachment. If it's a document, extracts text,
    or if it's an image, stores it for later analysis. Returns a structured result.
    """
    try:
        # Get the media type from the attachment metadata
        media_type: str = attachment.get("metadata", {}).get("mediaType", "")
        # Validate the attachment type
        if not validate_attachment_filetype(attachment):
            return AttachmentProcessingResult(
                text=None,
                file_blob=None,
                file_name=None,
                error=f"Unsupported file type: {media_type}",
            )

        attachment_link = _make_attachment_link(
            confluence_client, attachment, parent_content_id
        )
        if not attachment_link:
            return AttachmentProcessingResult(
                text=None, file_blob=None, file_name=None, error="Failed to make attachment link"
            )

        attachment_size = attachment["extensions"]["fileSize"]

        if media_type.startswith("image/"):
            if not allow_images:
                return AttachmentProcessingResult(
                    text=None,
                    file_blob=None,
                    file_name=None,
                    error="Image downloading is not enabled",
                )
        else:
            if attachment_size > CONFLUENCE_CONNECTOR_ATTACHMENT_SIZE_THRESHOLD:
                logging.warning(
                    f"Skipping {attachment_link} due to size. "
                    f"size={attachment_size} "
                    f"threshold={CONFLUENCE_CONNECTOR_ATTACHMENT_SIZE_THRESHOLD}"
                )
                return AttachmentProcessingResult(
                    text=None,
                    file_blob=None,
                    file_name=None,
                    error=f"Attachment text too long: {attachment_size} chars",
                )

        logging.info(
            f"Downloading attachment: "
            f"title={attachment['title']} "
            f"length={attachment_size} "
            f"link={attachment_link}"
        )

        # Download the attachment
        resp: requests.Response = confluence_client._session.get(attachment_link)
        if resp.status_code != 200:
            logging.warning(
                f"Failed to fetch {attachment_link} with status code {resp.status_code}"
            )
            return AttachmentProcessingResult(
                text=None,
                file_blob=None,
                file_name=None,
                error=f"Attachment download status code is {resp.status_code}",
            )

        raw_bytes = resp.content
        if not raw_bytes:
            return AttachmentProcessingResult(
                text=None, file_blob=None, file_name=None, error="attachment.content is None"
            )

        # Process image attachments
        if media_type.startswith("image/"):
            return _process_image_attachment(
                confluence_client, attachment, raw_bytes, media_type
            )

        # Process document attachments
        try:
            return AttachmentProcessingResult(text="",file_blob=raw_bytes, file_name=attachment.get("title", "unknown_title"), error=None)
        except Exception as e:
            logging.exception(e)
            return AttachmentProcessingResult(
                text=None, file_blob=None, file_name=None, error=f"Failed to extract text: {e}"
            )

    except Exception as e:
        return AttachmentProcessingResult(
            text=None, file_blob=None, file_name=None, error=f"Failed to process attachment: {e}"
        )