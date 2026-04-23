def _write_header(self, initlength):
        assert not self._headerwritten
        self._file.write(b'RIFF')
        if not self._nframes:
            self._nframes = initlength // (self._nchannels * self._sampwidth)
        self._datalength = self._nframes * self._nchannels * self._sampwidth
        try:
            self._form_length_pos = self._file.tell()
        except (AttributeError, OSError):
            self._form_length_pos = None
        has_fact = self._needs_fact_chunk()
        header_overhead = 36 + (12 if has_fact else 0)
        self._file.write(struct.pack('<L4s4sLHHLLHH',
            header_overhead + self._datalength + (self._datalength & 1), b'WAVE', b'fmt ', 16,
            self._format, self._nchannels, self._framerate,
            self._nchannels * self._framerate * self._sampwidth,
            self._nchannels * self._sampwidth,
            self._sampwidth * 8))
        if has_fact:
            self._file.write(b'fact')
            self._file.write(struct.pack('<L', 4))
            try:
                self._fact_sample_count_pos = self._file.tell()
            except (AttributeError, OSError):
                self._fact_sample_count_pos = None
            self._file.write(struct.pack('<L', self._nframes))
        self._file.write(b'data')
        if self._form_length_pos is not None:
            self._data_length_pos = self._file.tell()
        self._file.write(struct.pack('<L', self._datalength))
        self._headerwritten = True