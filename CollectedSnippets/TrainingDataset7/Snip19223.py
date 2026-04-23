def test_caches_set_with_timeout_as_none_set_non_expiring_key(self):
        """Memory caches that have the TIMEOUT parameter set to `None` will set
        a non expiring key by default.
        """
        key = "another-key"
        value = "another-value"
        cache = caches[DEFAULT_CACHE_ALIAS]
        cache.set(key, value)
        cache_key = cache.make_key(key)
        self.assertIsNone(cache._expire_info[cache_key])