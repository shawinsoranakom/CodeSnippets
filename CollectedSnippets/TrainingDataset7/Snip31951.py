def test_create_and_save(self):
        self.session = self.backend()
        self.session.create()
        self.session.save()
        self.assertIsNotNone(caches["default"].get(self.session.cache_key))