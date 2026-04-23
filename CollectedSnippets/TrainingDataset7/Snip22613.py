def test_integerfield_float(self):
        f = IntegerField()
        self.assertEqual(1, f.clean(1.0))
        self.assertEqual(1, f.clean("1.0"))
        self.assertEqual(1, f.clean(" 1.0 "))
        self.assertEqual(1, f.clean("1."))
        self.assertEqual(1, f.clean(" 1. "))
        with self.assertRaisesMessage(ValidationError, "'Enter a whole number.'"):
            f.clean("1.5")
        with self.assertRaisesMessage(ValidationError, "'Enter a whole number.'"):
            f.clean("…")