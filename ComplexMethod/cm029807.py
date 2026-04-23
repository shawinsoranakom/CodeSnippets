def read(self, size=None):
        self._checkReadable()
        if size is None:
            size = -1
        else:
            try:
                size_index = size.__index__
            except AttributeError:
                raise TypeError(f"{size!r} is not an integer")
            else:
                size = size_index()
        decoder = self._decoder or self._get_decoder()
        if size < 0:
            chunk = self.buffer.read()
            if chunk is None:
                raise BlockingIOError("Read returned None.")
            # Read everything.
            result = (self._get_decoded_chars() +
                      decoder.decode(chunk, final=True))
            if self._snapshot is not None:
                self._set_decoded_chars('')
                self._snapshot = None
            return result
        else:
            # Keep reading chunks until we have size characters to return.
            eof = False
            result = self._get_decoded_chars(size)
            while len(result) < size and not eof:
                eof = not self._read_chunk()
                result += self._get_decoded_chars(size - len(result))
            return result