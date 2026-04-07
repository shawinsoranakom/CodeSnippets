def test_caches_local(self):
        @async_to_sync
        async def async_cache():
            return caches[DEFAULT_CACHE_ALIAS]

        cache_1 = async_cache()
        cache_2 = async_cache()
        self.assertIs(cache_1, cache_2)