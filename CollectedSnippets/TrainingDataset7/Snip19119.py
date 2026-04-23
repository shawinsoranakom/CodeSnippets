def _perform_cull_test(self, cull_cache_name, initial_count, final_count):
        try:
            cull_cache = caches[cull_cache_name]
        except InvalidCacheBackendError:
            self.skipTest("Culling isn't implemented.")

        # Create initial cache key entries. This will overflow the cache,
        # causing a cull.
        for i in range(1, initial_count):
            cull_cache.set("cull%d" % i, "value", 1000)
        count = 0
        # Count how many keys are left in the cache.
        for i in range(1, initial_count):
            if cull_cache.has_key("cull%d" % i):
                count += 1
        self.assertEqual(count, final_count)