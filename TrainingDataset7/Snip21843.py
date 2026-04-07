def test_url_with_none_filename(self):
        storage = InMemoryStorage(base_url="/test_media_url/")
        self.assertEqual(storage.url(None), "/test_media_url/")