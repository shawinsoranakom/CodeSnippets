def test_non_string_input(self):
        self.assertEqual(urlize(123), "123")