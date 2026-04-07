def get(self, key, default=None, version=None):
        fname = self._key_to_file(key, version)
        try:
            with open(fname, "rb") as f:
                if not self._is_expired(f):
                    return pickle.loads(zlib.decompress(f.read()))
        except FileNotFoundError:
            pass
        return default