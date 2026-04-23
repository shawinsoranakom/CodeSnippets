def readall(self):
        """Read all data from the file, returned as bytes.

        Reads until either there is an error or read() returns size 0
        (indicates EOF). If the file is already at EOF, returns an
        empty bytes object.

        In non-blocking mode, returns as much data as could be read
        before EAGAIN. If no data is available (EAGAIN is returned
        before bytes are read) returns None.
        """
        self._checkClosed()
        self._checkReadable()
        if self._stat_atopen is None or self._stat_atopen.st_size <= 0:
            bufsize = DEFAULT_BUFFER_SIZE
        else:
            # In order to detect end of file, need a read() of at least 1
            # byte which returns size 0. Oversize the buffer by 1 byte so the
            # I/O can be completed with two read() calls (one for all data, one
            # for EOF) without needing to resize the buffer.
            bufsize = self._stat_atopen.st_size + 1

            if self._stat_atopen.st_size > 65536:
                try:
                    pos = os.lseek(self._fd, 0, SEEK_CUR)
                    if self._stat_atopen.st_size >= pos:
                        bufsize = self._stat_atopen.st_size - pos + 1
                except OSError:
                    pass

        result = bytearray(bufsize)
        bytes_read = 0
        try:
            while n := os.readinto(self._fd, memoryview(result)[bytes_read:]):
                bytes_read += n
                if bytes_read >= len(result):
                    result.resize(_new_buffersize(bytes_read))
        except BlockingIOError:
            if not bytes_read:
                return None

        assert len(result) - bytes_read >= 1, \
            "os.readinto buffer size 0 will result in erroneous EOF / returns 0"
        result.resize(bytes_read)
        return result.take_bytes()