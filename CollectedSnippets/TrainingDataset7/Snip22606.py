def test_integerfield_2(self):
        f = IntegerField(required=False)
        self.assertIsNone(f.clean(""))
        self.assertEqual("None", repr(f.clean("")))
        self.assertIsNone(f.clean(None))
        self.assertEqual("None", repr(f.clean(None)))
        self.assertEqual(1, f.clean("1"))
        self.assertIsInstance(f.clean("1"), int)
        self.assertEqual(23, f.clean("23"))
        with self.assertRaisesMessage(ValidationError, "'Enter a whole number.'"):
            f.clean("a")
        self.assertEqual(1, f.clean("1 "))
        self.assertEqual(1, f.clean(" 1"))
        self.assertEqual(1, f.clean(" 1 "))
        with self.assertRaisesMessage(ValidationError, "'Enter a whole number.'"):
            f.clean("1a")
        self.assertIsNone(f.max_value)
        self.assertIsNone(f.min_value)