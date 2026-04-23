def _build_document(self, entry: Any, updated_at: datetime) -> Document:
        link = (entry.get("link") or "").strip()
        title = (entry.get("title") or "").strip()
        stable_key = (entry.get("id") or link or title or self.feed_url).strip()
        semantic_identifier = title or link or stable_key
        content = self._build_content(entry, semantic_identifier)
        blob = content.encode("utf-8")

        metadata: dict[str, Any] = {"feed_url": self.feed_url}
        if link:
            metadata["link"] = link
        if entry.get("author"):
            metadata["author"] = entry.get("author")

        categories = []
        for tag in entry.get("tags", []):
            if not isinstance(tag, dict):
                continue
            term = tag.get("term")
            if isinstance(term, str) and term:
                categories.append(term)
        if categories:
            metadata["categories"] = categories

        return Document(
            id=f"rss:{hashlib.md5(stable_key.encode('utf-8')).hexdigest()}",
            source=DocumentSource.RSS,
            semantic_identifier=semantic_identifier,
            extension=".txt",
            blob=blob,
            doc_updated_at=updated_at,
            size_bytes=len(blob),
            metadata=metadata,
        )