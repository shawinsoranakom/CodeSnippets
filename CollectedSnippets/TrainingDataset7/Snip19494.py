def test_static_url_no_slash(self):
        self.assertEqual(check_url_settings(None), [E006("STATIC_URL")])