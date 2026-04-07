def test_non_string_input(self):
        self.assertEqual(addslashes(123), "123")