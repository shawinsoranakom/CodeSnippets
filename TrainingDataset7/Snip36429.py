def test_invalid_literal(self):
        for n in ["#", " "]:
            with self.assertRaisesMessage(
                ValueError, "invalid literal for int() with base 36: '%s'" % n
            ):
                base36_to_int(n)