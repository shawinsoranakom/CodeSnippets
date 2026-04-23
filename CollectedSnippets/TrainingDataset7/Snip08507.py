def __init__(self, content="", name=None):
        super().__init__(content, name)
        self._content_type = type(content)
        self._initialize_times()