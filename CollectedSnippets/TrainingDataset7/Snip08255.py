def get(self, key, default=None, version=None):
        self.make_and_validate_key(key, version=version)
        return default