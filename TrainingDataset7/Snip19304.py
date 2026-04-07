async def test_aset_many_invalid_key(self):
        msg = KEY_ERRORS_WITH_MEMCACHED_MSG % ":1:key with spaces"
        with self.assertWarnsMessage(CacheKeyWarning, msg):
            await cache.aset_many({"key with spaces": "foo"})