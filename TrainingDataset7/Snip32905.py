def test_non_string_input(self):
        self.assertEqual(escape(123), "123")