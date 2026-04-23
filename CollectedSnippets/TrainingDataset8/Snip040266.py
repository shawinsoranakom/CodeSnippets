def test_cache_clear_all_caches(
        self, clear_singleton_cache, clear_memo_cache, clear_legacy_cache
    ):
        """cli.clear_cache should clear st.cache, st.memo and st.singleton"""
        self.runner.invoke(cli, ["cache", "clear"])
        clear_singleton_cache.assert_called_once()
        clear_memo_cache.assert_called_once()
        clear_legacy_cache.assert_called_once()