def data(self, data: RequestData):
        # Try catch some common mistakes
        if data is not None and (
            not isinstance(data, (bytes, io.IOBase, Iterable)) or isinstance(data, (str, Mapping))
        ):
            raise TypeError('data must be bytes, iterable of bytes, or a file-like object')

        if data == self._data and self._data is None:
            self.headers.pop('Content-Length', None)

        # https://docs.python.org/3/library/urllib.request.html#urllib.request.Request.data
        if data != self._data:
            if self._data is not None:
                self.headers.pop('Content-Length', None)
            self._data = data

        if self._data is None:
            self.headers.pop('Content-Type', None)

        if 'Content-Type' not in self.headers and self._data is not None:
            self.headers['Content-Type'] = 'application/x-www-form-urlencoded'