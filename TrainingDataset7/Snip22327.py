def test_get_absolute_url_include_no_slash(self):
        self.assertEqual(self.page.get_absolute_url(), "/flatpagecaf%C3%A9/")