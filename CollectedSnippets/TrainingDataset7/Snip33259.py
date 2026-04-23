def test_non_string_input(self):
        self.assertEqual(wordwrap(123, 2), "123")