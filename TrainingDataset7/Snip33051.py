def test_non_string_input(self):
        self.assertEqual(rjust(123, 4), " 123")