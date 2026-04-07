def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        self.make_and_validate_key(key, version=version)