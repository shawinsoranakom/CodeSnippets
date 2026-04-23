def _detect_file_extension(self, content) -> str:
        """Detect file extension based on content headers."""
        if isinstance(content, bytes):
            # Check magic numbers for common file types
            if content.startswith(b"\xff\xd8\xff"):
                return ".jpg"
            if content.startswith(b"\x89PNG\r\n\x1a\n"):
                return ".png"
            if content.startswith((b"GIF87a", b"GIF89a")):
                return ".gif"
            if content.startswith(b"%PDF"):
                return ".pdf"
            if content.startswith(b"PK\x03\x04"):  # ZIP/DOCX/XLSX
                return ".zip"
            if content.startswith(b"\x00\x00\x01\x00"):  # ICO
                return ".ico"
            if content.startswith(b"RIFF") and b"WEBP" in content[:12]:
                return ".webp"
            if content.startswith((b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")):
                return ".mp3"
            if content.startswith((b"ftypmp4", b"\x00\x00\x00\x20ftypmp4")):
                return ".mp4"
            # Try to decode as text
            try:
                content.decode("utf-8")
                return ".txt"  # noqa: TRY300
            except UnicodeDecodeError:
                return ".bin"  # Binary file
        else:
            # String content
            return ".txt"