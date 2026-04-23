def test_negative_number(self):
        with self.assertRaisesMessage(
            ValueError, "'number' must be greater or equal to 0."
        ):
            Repeat("name", -1)