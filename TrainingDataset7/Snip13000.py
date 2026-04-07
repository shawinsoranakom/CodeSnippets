def _set_streaming_content(self, value):
        if not hasattr(value, "read"):
            self.file_to_stream = None
            return super()._set_streaming_content(value)

        self.file_to_stream = filelike = value
        if hasattr(filelike, "close"):
            self._resource_closers.append(filelike.close)
        value = iter(lambda: filelike.read(self.block_size), b"")
        self.set_headers(filelike)
        super()._set_streaming_content(value)