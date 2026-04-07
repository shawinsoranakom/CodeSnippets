def test_memcached_deletes_key_on_failed_set(self):
        # By default memcached allows objects up to 1MB. For the cache_db
        # session backend to always use the current session, memcached needs to
        # delete the old key if it fails to set.
        max_value_length = 2**20

        cache.set("small_value", "a")
        self.assertEqual(cache.get("small_value"), "a")

        large_value = "a" * (max_value_length + 1)
        try:
            cache.set("small_value", large_value)
        except Exception:
            # Most clients (e.g. pymemcache or pylibmc) raise when the value is
            # too large. This test is primarily checking that the key was
            # deleted, so the return/exception behavior for the set() itself is
            # not important.
            pass
        # small_value should be deleted, or set if configured to accept larger
        # values
        value = cache.get("small_value")
        self.assertTrue(value is None or value == large_value)