def delete_many(self, keys, version=None):
        keys = [self.make_and_validate_key(key, version=version) for key in keys]
        self._base_delete_many(keys)