def test_get_absolute_url_urlencodes(self):
        self.assertEqual(self.page.get_absolute_url(), "/caf%C3%A9/")