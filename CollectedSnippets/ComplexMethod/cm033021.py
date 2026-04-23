def _build_attachment_document(
        self,
        block_id: str,
        url: str,
        name: str,
        caption: Optional[str],
        page_last_edited_time: Optional[str],
        page_path: Optional[str],
    ) -> Document | None:
        file_bytes = self._download_file(url)
        if file_bytes is None:
            return None

        extension = Path(name).suffix or Path(urlparse(url).path).suffix or ".bin"
        if extension and not extension.startswith("."):
            extension = f".{extension}"
        if not extension:
            extension = ".bin"

        updated_at = datetime_from_string(page_last_edited_time) if page_last_edited_time else datetime.now(timezone.utc)
        base_identifier = name or caption or (f"Notion file {block_id}" if block_id else "Notion file")
        semantic_identifier = f"{page_path} / {base_identifier}" if page_path else base_identifier

        return Document(
            id=block_id,
            blob=file_bytes,
            source=DocumentSource.NOTION,
            semantic_identifier=semantic_identifier,
            extension=extension,
            size_bytes=len(file_bytes),
            doc_updated_at=updated_at,
        )