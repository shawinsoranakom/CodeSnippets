def test_valid_url(self, url, expected_value):
        if expected_value:
            self.assertTrue(valid_url(url))
        else:
            self.assertFalse(valid_url(url))