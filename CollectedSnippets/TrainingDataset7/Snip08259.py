def has_key(self, key, version=None):
        self.make_and_validate_key(key, version=version)
        return False