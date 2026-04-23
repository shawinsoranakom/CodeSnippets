def _read_fmt_chunk(self, chunk):
        try:
            self._format, self._nchannels, self._framerate, dwAvgBytesPerSec, wBlockAlign = struct.unpack_from('<HHLLH', chunk.read(14))
        except struct.error:
            raise EOFError from None
        if self._format not in (WAVE_FORMAT_PCM, WAVE_FORMAT_IEEE_FLOAT, WAVE_FORMAT_EXTENSIBLE):
            raise Error('unknown format: %r' % (self._format,))
        try:
            sampwidth = struct.unpack_from('<H', chunk.read(2))[0]
        except struct.error:
            raise EOFError from None
        if self._format == WAVE_FORMAT_EXTENSIBLE:
            try:
                cbSize, wValidBitsPerSample, dwChannelMask = struct.unpack_from('<HHL', chunk.read(8))
                # Read the entire UUID from the chunk
                SubFormat = chunk.read(16)
                if len(SubFormat) < 16:
                    raise EOFError
            except struct.error:
                raise EOFError from None
            if SubFormat != KSDATAFORMAT_SUBTYPE_PCM:
                try:
                    import uuid
                    subformat_msg = f'unknown extended format: {uuid.UUID(bytes_le=SubFormat)}'
                except Exception:
                    subformat_msg = 'unknown extended format'
                raise Error(subformat_msg)
        self._sampwidth = (sampwidth + 7) // 8
        if not self._sampwidth:
            raise Error('bad sample width')
        if not self._nchannels:
            raise Error('bad # of channels')
        self._framesize = self._nchannels * self._sampwidth
        self._comptype = 'NONE'
        self._compname = 'not compressed'