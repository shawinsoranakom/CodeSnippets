def seek(self, cookie, whence=0):
        def _reset_encoder(position):
            """Reset the encoder (merely useful for proper BOM handling)"""
            try:
                encoder = self._encoder or self._get_encoder()
            except LookupError:
                # Sometimes the encoder doesn't exist
                pass
            else:
                if position != 0:
                    encoder.setstate(0)
                else:
                    encoder.reset()

        if self.closed:
            raise ValueError("tell on closed file")
        if not self._seekable:
            raise UnsupportedOperation("underlying stream is not seekable")
        if whence == SEEK_CUR:
            if cookie != 0:
                raise UnsupportedOperation("can't do nonzero cur-relative seeks")
            # Seeking to the current position should attempt to
            # sync the underlying buffer with the current position.
            whence = 0
            cookie = self.tell()
        elif whence == SEEK_END:
            if cookie != 0:
                raise UnsupportedOperation("can't do nonzero end-relative seeks")
            self.flush()
            position = self.buffer.seek(0, whence)
            self._set_decoded_chars('')
            self._snapshot = None
            if self._decoder:
                self._decoder.reset()
            _reset_encoder(position)
            return position
        if whence != 0:
            raise ValueError("unsupported whence (%r)" % (whence,))
        if cookie < 0:
            raise ValueError("negative seek position %r" % (cookie,))
        self.flush()

        # The strategy of seek() is to go back to the safe start point
        # and replay the effect of read(chars_to_skip) from there.
        start_pos, dec_flags, bytes_to_feed, need_eof, chars_to_skip = \
            self._unpack_cookie(cookie)

        # Seek back to the safe start point.
        self.buffer.seek(start_pos)
        self._set_decoded_chars('')
        self._snapshot = None

        # Restore the decoder to its state from the safe start point.
        if cookie == 0 and self._decoder:
            self._decoder.reset()
        elif self._decoder or dec_flags or chars_to_skip:
            self._decoder = self._decoder or self._get_decoder()
            self._decoder.setstate((b'', dec_flags))
            self._snapshot = (dec_flags, b'')

        if chars_to_skip:
            # Just like _read_chunk, feed the decoder and save a snapshot.
            input_chunk = self.buffer.read(bytes_to_feed)
            self._set_decoded_chars(
                self._decoder.decode(input_chunk, need_eof))
            self._snapshot = (dec_flags, input_chunk)

            # Skip chars_to_skip of the decoded characters.
            if len(self._decoded_chars) < chars_to_skip:
                raise OSError("can't restore logical file position")
            self._decoded_chars_used = chars_to_skip

        _reset_encoder(cookie)
        return cookie