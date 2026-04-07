def _set_streaming_content(self, value):
        # Ensure we can never iterate on "value" more than once.
        try:
            self._iterator = iter(value)
            self.is_async = False
        except TypeError:
            self._iterator = aiter(value)
            self.is_async = True
        if hasattr(value, "close"):
            self._resource_closers.append(value.close)