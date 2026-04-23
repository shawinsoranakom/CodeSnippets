def _readinto(self, buf, read1):
        """Read data into *buf* with at most one system call."""

        self._checkClosed("readinto of closed file")

        # Need to create a memoryview object of type 'b', otherwise
        # we may not be able to assign bytes to it, and slicing it
        # would create a new object.
        if not isinstance(buf, memoryview):
            buf = memoryview(buf)
        if buf.nbytes == 0:
            return 0
        buf = buf.cast('B')

        written = 0
        with self._read_lock:
            while written < len(buf):

                # First try to read from internal buffer
                avail = min(len(self._read_buf) - self._read_pos, len(buf))
                if avail:
                    buf[written:written+avail] = \
                        self._read_buf[self._read_pos:self._read_pos+avail]
                    self._read_pos += avail
                    written += avail
                    if written == len(buf):
                        break

                # If remaining space in callers buffer is larger than
                # internal buffer, read directly into callers buffer
                if len(buf) - written > self.buffer_size:
                    n = self.raw.readinto(buf[written:])
                    if not n:
                        break # eof
                    written += n

                # Otherwise refill internal buffer - unless we're
                # in read1 mode and already got some data
                elif not (read1 and written):
                    if not self._peek_unlocked(1):
                        break # eof

                # In readinto1 mode, return as soon as we have some data
                if read1 and written:
                    break

        return written