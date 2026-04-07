def delete(self, key, version=None):
        return self._delete(self._key_to_file(key, version))