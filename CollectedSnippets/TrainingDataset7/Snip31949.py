def test_default_cache(self):
        self.session.save()
        self.assertIsNotNone(caches["default"].get(self.session.cache_key))