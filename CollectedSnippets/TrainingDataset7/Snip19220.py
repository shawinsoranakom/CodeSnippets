def test_caches_with_unset_timeout_has_correct_default_timeout(self):
        """Caches that have the TIMEOUT parameter undefined in the default
        settings will use the default 5 minute timeout.
        """
        cache = caches[DEFAULT_CACHE_ALIAS]
        self.assertEqual(self.DEFAULT_TIMEOUT, cache.default_timeout)