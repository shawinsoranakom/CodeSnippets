def extract_attachments(email_msg: Message, max_bytes: int = IMAP_CONNECTOR_SIZE_THRESHOLD):
    attachments = []

    if not email_msg.is_multipart():
        return attachments

    for part in email_msg.walk():
        if part.get_content_maintype() == "multipart":
            continue

        disposition = (part.get("Content-Disposition") or "").lower()
        filename = part.get_filename()

        if not (
            disposition.startswith("attachment")
            or (disposition.startswith("inline") and filename)
        ):
            continue

        payload = part.get_payload(decode=True)
        if not payload:
            continue

        if len(payload) > max_bytes:
            continue

        attachments.append({
            "filename": filename or "attachment.bin",
            "content_type": part.get_content_type(),
            "content_bytes": payload,
            "size_bytes": len(payload),
        })

    return attachments