def test_integer_literals(self):
        self.assertEqual(
            Variable("999999999999999999999999999").literal, 999999999999999999999999999
        )