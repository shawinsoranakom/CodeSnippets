def test_media_url_no_slash(self):
        self.assertEqual(check_url_settings(None), [E006("MEDIA_URL")])