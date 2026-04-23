def _attachment_to_document(self, issue: Issue, attachment: dict[str, Any]) -> Document | None:
        if not self.include_attachments:
            return None

        filename = attachment.get("filename")
        content_url = attachment.get("content")
        if not filename or not content_url:
            return None

        try:
            attachment_size = int(attachment.get("size", 0))
        except (TypeError, ValueError):
            attachment_size = 0
        if attachment_size and attachment_size > self.attachment_size_limit:
            logger.info(f"[Jira] Skipping attachment {filename} on {issue.key} because reported size exceeds limit ({self.attachment_size_limit} bytes).")
            return None

        blob = self._download_attachment(content_url)
        if blob is None:
            return None

        if len(blob) > self.attachment_size_limit:
            logger.info(f"[Jira] Skipping attachment {filename} on {issue.key} because it exceeds the size limit ({self.attachment_size_limit} bytes).")
            return None

        attachment_time = parse_jira_datetime(attachment.get("created")) or parse_jira_datetime(attachment.get("updated"))
        updated_dt = attachment_time or parse_jira_datetime(issue.raw.get("fields", {}).get("updated")) or datetime.now(timezone.utc)

        extension = os.path.splitext(filename)[1] or ""
        document_id = f"{issue.key}::attachment::{attachment.get('id') or filename}"
        semantic_identifier = f"{issue.key} attachment: {filename}"

        return Document(
            id=document_id,
            source=DocumentSource.JIRA,
            semantic_identifier=semantic_identifier,
            extension=extension,
            blob=blob,
            doc_updated_at=updated_dt,
            size_bytes=len(blob),
        )