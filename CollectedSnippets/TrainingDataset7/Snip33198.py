def test_non_string_input(self):
        self.assertEqual(urlencode(1), "1")