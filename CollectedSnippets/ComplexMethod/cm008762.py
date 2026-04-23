def read(self, size=None):
        exception_raised = True
        try:
            while self._iterator and (size is None or len(self._buffer) < size):
                chunk = next(self._iterator, None)
                if chunk is None:
                    self._iterator = None
                    break
                self._buffer += chunk
                self.bytes_read += len(chunk)

            if size is None:
                size = len(self._buffer)
            data = self._buffer[:size]
            self._buffer = self._buffer[size:]

            # "free" the curl instance if the response is fully read.
            # curl_cffi doesn't do this automatically and only allows one open response per thread
            if not self._iterator and not self._buffer:
                self.close()
            exception_raised = False
            return data
        finally:
            if exception_raised:
                self.close()