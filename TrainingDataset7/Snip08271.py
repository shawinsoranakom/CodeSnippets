def _createdir(self):
        # Workaround because os.makedirs() doesn't apply the "mode" argument
        # to intermediate-level directories.
        # https://github.com/python/cpython/issues/86533
        safe_makedirs(self._dir, mode=0o700, exist_ok=True)