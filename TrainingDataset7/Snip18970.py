def write(self, data):
        """'write()' callable as specified by PEP 3333"""

        assert isinstance(data, bytes), "write() argument must be bytestring"

        if not self.status:
            raise AssertionError("write() before start_response()")

        elif not self.headers_sent:
            # Before the first output, send the stored headers
            self.bytes_sent = len(data)  # make sure we know content-length
            self.send_headers()
        else:
            self.bytes_sent += len(data)

        # XXX check Content-Length and truncate if too many bytes written?
        data = BytesIO(data)
        for chunk in iter(lambda: data.read(MAX_SOCKET_CHUNK_SIZE), b""):
            self._write(chunk)
            self._flush()