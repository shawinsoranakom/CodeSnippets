def __iter__(self):
        if not self._is_rendered:
            raise ContentNotRenderedError(
                "The response content must be rendered before it can be iterated over."
            )
        return super().__iter__()