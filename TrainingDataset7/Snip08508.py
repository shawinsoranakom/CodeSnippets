def open(self, mode):
        self._convert_stream_content(mode)
        self._update_accessed_time()
        return super().open(mode)