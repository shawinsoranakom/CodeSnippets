def test_get_absolute_url_include(self):
        self.assertEqual(self.page.get_absolute_url(), "/flatpage_root/caf%C3%A9/")