def test_non_string_input(self):
        self.assertEqual(cut(123, "2"), "13")