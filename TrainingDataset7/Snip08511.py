def _convert_stream_content(self, mode):
        """Convert actual file content according to the opening mode."""
        new_content_type = bytes if "b" in mode else str
        # No conversion needed.
        if self._content_type == new_content_type:
            return

        content = self.file.getvalue()
        content = content.encode() if isinstance(content, str) else content.decode()
        self._content_type = new_content_type
        self._initialize_stream()

        self.file.write(content)