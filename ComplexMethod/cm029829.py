def get_message(self, key):
        """Return a Message representation or raise a KeyError."""
        start, stop = self._lookup(key)
        self._file.seek(start)
        self._file.readline()   # Skip b'1,' line specifying labels.
        original_headers = io.BytesIO()
        while True:
            line = self._file.readline()
            if line == b'*** EOOH ***' + linesep or not line:
                break
            original_headers.write(line.replace(linesep, b'\n'))
        visible_headers = io.BytesIO()
        while True:
            line = self._file.readline()
            if line == linesep or not line:
                break
            visible_headers.write(line.replace(linesep, b'\n'))
        # Read up to the stop, or to the end
        n = stop - self._file.tell()
        assert n >= 0
        body = self._file.read(n)
        body = body.replace(linesep, b'\n')
        msg = BabylMessage(original_headers.getvalue() + body)
        msg.set_visible(visible_headers.getvalue())
        if key in self._labels:
            msg.set_labels(self._labels[key])
        return msg