def validate_key(self, key):
        for warning in memcache_key_warnings(key):
            raise InvalidCacheKey(warning)