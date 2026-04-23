def _get_file_content(self, file_ref: str) -> tuple[bytes, str]:
        """
        Get file content from a variable reference.
        Returns (content_bytes, filename).
        """
        value = self._canvas.get_variable_value(file_ref)
        if value is None:
            return None, None

        # Handle different value formats
        if isinstance(value, dict):
            # File reference from Begin/UserFillUp component
            file_id = value.get("id") or value.get("file_id")
            created_by = value.get("created_by") or self._canvas.get_tenant_id()
            filename = value.get("name") or value.get("filename", "unknown.xlsx")
            if file_id:
                content = FileService.get_blob(created_by, file_id)
                return content, filename
        elif isinstance(value, list) and len(value) > 0:
            # List of file references - return first
            return self._get_file_content_from_list(value[0])
        elif isinstance(value, str):
            # Could be base64 encoded or a path
            if value.startswith("data:"):
                import base64
                # Extract base64 content
                _, encoded = value.split(",", 1)
                return base64.b64decode(encoded), "uploaded.xlsx"

        return None, None