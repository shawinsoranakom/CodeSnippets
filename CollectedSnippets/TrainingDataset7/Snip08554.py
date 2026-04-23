def __init__(self, name, content, content_type="text/plain"):
        content = content or b""
        super().__init__(
            BytesIO(content), None, name, content_type, len(content), None, None
        )