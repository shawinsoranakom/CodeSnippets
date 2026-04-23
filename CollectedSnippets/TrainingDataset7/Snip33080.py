def test_non_string_input(self):
        self.assertEqual(striptags(123), "123")