def content(self, value):
        if value:
            raise AttributeError(
                "You cannot set content to a 304 (Not Modified) response"
            )
        self._container = []