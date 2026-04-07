def test_non_string_input(self):
        self.assertEqual(truncatewords(123, 2), "123")