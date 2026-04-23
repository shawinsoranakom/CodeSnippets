def test_negative_input(self):
        with self.assertRaisesMessage(ValueError, "Negative base36 conversion input."):
            int_to_base36(-1)