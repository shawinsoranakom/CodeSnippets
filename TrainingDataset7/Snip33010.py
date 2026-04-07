def test_non_string_input(self):
        self.assertEqual(linenumbers(123), "1. 123")