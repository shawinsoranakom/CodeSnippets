def test_delete_many_invalid_key(self):
        msg = KEY_ERRORS_WITH_MEMCACHED_MSG % ":1:key with spaces"
        with self.assertWarnsMessage(CacheKeyWarning, msg):
            cache.delete_many(["key with spaces"])