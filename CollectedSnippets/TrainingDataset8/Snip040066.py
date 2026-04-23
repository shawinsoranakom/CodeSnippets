def test_invalidate_pages_cache(self):
        source_util.invalidate_pages_cache()

        assert source_util._cached_pages is None
        source_util._on_pages_changed.send.assert_called_once()