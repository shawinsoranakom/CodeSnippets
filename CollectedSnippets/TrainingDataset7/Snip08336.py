def get_many(self, keys, version=None):
        key_map = {
            self.make_and_validate_key(key, version=version): key for key in keys
        }
        ret = self._cache.get_many(key_map.keys())
        return {key_map[k]: v for k, v in ret.items()}