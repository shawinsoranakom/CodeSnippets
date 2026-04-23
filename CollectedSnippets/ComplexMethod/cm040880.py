def read(self, size=-1):
        """
        Read from the underlying stream, and return at most `size` decoded bytes.
        If a chunk is smaller than `size`, we will return less than asked, but we will always return data if there
        are chunks left
        :param size: amount to read, please note that it can return less than asked
        :return: bytes from the underlying stream
        """
        if size < 0:
            return self.readall()

        if not size:
            return b""

        if self._end_chunk:
            # if it's the end of a chunk we need to strip the newline at the end of the chunk
            # before jumping to the new one
            self._strip_chunk_new_lines()
            self._new_chunk = True
            self._end_chunk = False

        if self._new_chunk:
            # If the _new_chunk flag is set, we have to jump to the next chunk, if there's one
            self._get_next_chunk_length()
            self._new_chunk = False

        if self._chunk_size == 0 and self._decoded_length <= 0:
            # If the next chunk is 0, and we decoded everything, try to get the trailing headers
            self._get_trailing_headers()
            if self.s3_object:
                self._set_checksum_value()
            return b""

        # take the minimum account between the requested size, and the left chunk size
        # (to not over read from the chunk)
        amount = min(self._chunk_size, size)
        data = self._stream.read(amount)

        if data == b"":
            raise EOFError("Encoded file ended before the end-of-stream marker was reached")

        read = len(data)
        self._chunk_size -= read
        if self._chunk_size <= 0:
            self._end_chunk = True

        self._decoded_length -= read

        return data