def test_non_string_input(self):
        self.assertEqual(slugify(123), "123")