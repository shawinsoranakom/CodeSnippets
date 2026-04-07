def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        self._createdir()  # Cache dir can be deleted at any time.
        fname = self._key_to_file(key, version)
        self._cull()  # make some room if necessary
        fd, tmp_path = tempfile.mkstemp(dir=self._dir)
        renamed = False
        try:
            with open(fd, "wb") as f:
                self._write_content(f, timeout, value)
            file_move_safe(tmp_path, fname, allow_overwrite=True)
            renamed = True
        finally:
            if not renamed:
                os.remove(tmp_path)