def test_input_too_large(self):
        with self.assertRaisesMessage(ValueError, "Base36 input too large"):
            base36_to_int("1" * 14)