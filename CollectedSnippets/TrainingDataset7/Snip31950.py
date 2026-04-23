def test_non_default_cache(self):
        # Re-initialize the session backend to make use of overridden settings.
        self.session = self.backend()

        self.session.save()
        self.assertIsNone(caches["default"].get(self.session.cache_key))
        self.assertIsNotNone(caches["sessions"].get(self.session.cache_key))