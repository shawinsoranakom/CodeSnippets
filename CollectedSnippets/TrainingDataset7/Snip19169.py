def setUp(self):
        super().setUp()

        # LocMem requires a hack to make the other caches
        # share a data store with the 'normal' cache.
        caches["prefix"]._cache = cache._cache
        caches["prefix"]._expire_info = cache._expire_info

        caches["v2"]._cache = cache._cache
        caches["v2"]._expire_info = cache._expire_info

        caches["custom_key"]._cache = cache._cache
        caches["custom_key"]._expire_info = cache._expire_info

        caches["custom_key2"]._cache = cache._cache
        caches["custom_key2"]._expire_info = cache._expire_info