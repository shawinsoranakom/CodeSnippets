def test_no_warnings(self):
        result = check_url_config(None)
        self.assertEqual(result, [])