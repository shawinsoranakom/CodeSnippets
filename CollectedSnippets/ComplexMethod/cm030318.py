def _read1(self, n):
        # Read up to n compressed bytes with at most one read() system call,
        # decrypt and decompress them.
        if self._eof or n <= 0:
            return b''

        # Read from file.
        if self._compress_type == ZIP_DEFLATED:
            ## Handle unconsumed data.
            data = self._decompressor.unconsumed_tail
            if n > len(data):
                data += self._read2(n - len(data))
        else:
            data = self._read2(n)

        if self._compress_type == ZIP_STORED:
            self._eof = self._compress_left <= 0
        elif self._compress_type == ZIP_DEFLATED:
            n = max(n, self.MIN_READ_SIZE)
            data = self._decompressor.decompress(data, n)
            self._eof = (self._decompressor.eof or
                         self._compress_left <= 0 and
                         not self._decompressor.unconsumed_tail)
            if self._eof:
                data += self._decompressor.flush()
        else:
            data = self._decompressor.decompress(data)
            self._eof = self._decompressor.eof or self._compress_left <= 0

        data = data[:self._left]
        self._left -= len(data)
        if self._left <= 0:
            self._eof = True
        self._update_crc(data)
        return data