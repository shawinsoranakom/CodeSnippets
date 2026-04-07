async def test_adelete_many_invalid_key(self):
        msg = KEY_ERRORS_WITH_MEMCACHED_MSG % ":1:key with spaces"
        with self.assertWarnsMessage(CacheKeyWarning, msg):
            await cache.adelete_many({"key with spaces": "foo"})