def __enter__(self):
        self._path = tempfile.mkdtemp(*self._args, **self._kwargs)
        return self._path