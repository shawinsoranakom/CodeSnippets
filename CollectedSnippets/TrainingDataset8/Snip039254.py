def test_clear_cache_all_caches(
        self, clear_singleton_cache, clear_memo_cache, clear_legacy_cache
    ):
        session = _create_test_session()
        session._handle_clear_cache_request()
        clear_singleton_cache.assert_called_once()
        clear_memo_cache.assert_called_once()
        clear_legacy_cache.assert_called_once()