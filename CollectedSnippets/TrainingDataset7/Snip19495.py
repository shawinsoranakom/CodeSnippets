def test_static_url_double_slash_allowed(self):
        # The check allows for a double slash, presuming the user knows what
        # they are doing.
        self.assertEqual(check_url_settings(None), [])