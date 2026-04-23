def seek(self, offset, whence=os.SEEK_SET):
        if self.closed:
            raise ValueError("seek on closed file.")
        if not self._seekable:
            raise io.UnsupportedOperation("underlying stream is not seekable")
        curr_pos = self.tell()
        if whence == os.SEEK_SET:
            new_pos = offset
        elif whence == os.SEEK_CUR:
            new_pos = curr_pos + offset
        elif whence == os.SEEK_END:
            new_pos = self._orig_file_size + offset
        else:
            raise ValueError("whence must be os.SEEK_SET (0), "
                             "os.SEEK_CUR (1), or os.SEEK_END (2)")

        if new_pos > self._orig_file_size:
            new_pos = self._orig_file_size

        if new_pos < 0:
            new_pos = 0

        read_offset = new_pos - curr_pos
        buff_offset = read_offset + self._offset

        if buff_offset >= 0 and buff_offset < len(self._readbuffer):
            # Just move the _offset index if the new position is in the _readbuffer
            self._offset = buff_offset
            read_offset = 0
        # Fast seek uncompressed unencrypted file
        elif self._compress_type == ZIP_STORED and self._decrypter is None and read_offset != 0:
            # disable CRC checking after first seeking - it would be invalid
            self._expected_crc = None
            # seek actual file taking already buffered data into account
            read_offset -= len(self._readbuffer) - self._offset
            self._fileobj.seek(read_offset, os.SEEK_CUR)
            self._left -= read_offset
            self._compress_left -= read_offset
            self._eof = self._left <= 0
            read_offset = 0
            # flush read buffer
            self._readbuffer = b''
            self._offset = 0
        elif read_offset < 0:
            # Position is before the current position. Reset the ZipExtFile
            self._fileobj.seek(self._orig_compress_start)
            self._running_crc = self._orig_start_crc
            self._expected_crc = self._orig_crc
            self._compress_left = self._orig_compress_size
            self._left = self._orig_file_size
            self._readbuffer = b''
            self._offset = 0
            self._decompressor = _get_decompressor(self._compress_type)
            self._eof = False
            read_offset = new_pos
            if self._decrypter is not None:
                self._init_decrypter()

        while read_offset > 0:
            read_len = min(self.MAX_SEEK_READ, read_offset)
            self.read(read_len)
            read_offset -= read_len

        return self.tell()