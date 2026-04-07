def test_empty_string_no_errors(self):
        self.assertEqual(check_url_settings(None), [])