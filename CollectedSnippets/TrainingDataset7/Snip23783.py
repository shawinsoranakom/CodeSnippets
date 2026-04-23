def test_invalid_url(self):
        with self.assertRaises(AttributeError):
            self.client.get("/detail/author/invalid/url/")