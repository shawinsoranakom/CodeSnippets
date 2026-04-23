def test_cull_delete_when_store_empty(self):
        try:
            cull_cache = caches["cull"]
        except InvalidCacheBackendError:
            self.skipTest("Culling isn't implemented.")
        old_max_entries = cull_cache._max_entries
        # Force _cull to delete on first cached record.
        cull_cache._max_entries = -1
        try:
            cull_cache.set("force_cull_delete", "value", 1000)
            self.assertIs(cull_cache.has_key("force_cull_delete"), True)
        finally:
            cull_cache._max_entries = old_max_entries