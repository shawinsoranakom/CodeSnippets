def __init__(self, content, name=None):
        stream_class = StringIO if isinstance(content, str) else BytesIO
        super().__init__(stream_class(content), name=name)
        self.size = len(content)