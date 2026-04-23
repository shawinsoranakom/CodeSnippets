def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        try:
            with open(self._key_to_file(key, version), "r+b") as f:
                try:
                    locks.lock(f, locks.LOCK_EX)
                    if self._is_expired(f):
                        return False
                    else:
                        previous_value = pickle.loads(zlib.decompress(f.read()))
                        f.seek(0)
                        self._write_content(f, timeout, previous_value)
                        return True
                finally:
                    locks.unlock(f)
        except FileNotFoundError:
            return False