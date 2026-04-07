def test_default_cache_included(self):
        """
        Don't error if 'default' is present in CACHES setting.
        """
        self.assertEqual(check_default_cache_is_configured(None), [])