def _normalize_attachment_type(self, name: str, mime_type: str) -> str:
        mime_type = str(mime_type or "").strip().lower()
        if mime_type.startswith("image/"):
            return "image"
        if mime_type == "application/pdf":
            return "pdf"
        if mime_type == "text/csv":
            return "csv"
        if mime_type == "application/json":
            return "json"
        if mime_type == "text/html":
            return "html"

        ext = os.path.splitext(name or "")[1].lower().lstrip(".")
        return ext or "file"