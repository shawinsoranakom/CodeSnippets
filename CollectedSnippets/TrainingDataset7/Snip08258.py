def delete(self, key, version=None):
        self.make_and_validate_key(key, version=version)
        return False