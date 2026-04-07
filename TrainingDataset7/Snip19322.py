def test_default_cache_not_included(self):
        """
        Error if 'default' not present in CACHES setting.
        """
        self.assertEqual(check_default_cache_is_configured(None), [E001])