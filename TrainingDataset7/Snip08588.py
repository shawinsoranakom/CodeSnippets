def close(self):
        super().close()
        self._stream.close()