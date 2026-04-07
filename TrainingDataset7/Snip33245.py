def test_non_string_input(self):
        self.assertEqual(urlizetrunc(123, 1), "123")