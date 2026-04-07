def content(self):
        if not self._is_rendered:
            raise ContentNotRenderedError(
                "The response content must be rendered before it can be accessed."
            )
        return super().content