def readframes(self, nframes):
        if self._data_seek_needed:
            self._data_chunk.seek(0, 0)
            pos = self._soundpos * self._framesize
            if pos:
                self._data_chunk.seek(pos, 0)
            self._data_seek_needed = 0
        if nframes == 0:
            return b''
        data = self._data_chunk.read(nframes * self._framesize)
        if self._sampwidth != 1 and sys.byteorder == 'big':
            data = _byteswap(data, self._sampwidth)
        if self._convert and data:
            data = self._convert(data)
        self._soundpos = self._soundpos + len(data) // (self._nchannels * self._sampwidth)
        return data