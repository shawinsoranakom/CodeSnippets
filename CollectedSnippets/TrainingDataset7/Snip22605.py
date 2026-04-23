def test_integerfield_1(self):
        f = IntegerField()
        self.assertWidgetRendersTo(
            f, '<input type="number" name="f" id="id_f" required>'
        )
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean("")
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(None)
        self.assertEqual(1, f.clean("1"))
        self.assertIsInstance(f.clean("1"), int)
        self.assertEqual(23, f.clean("23"))
        with self.assertRaisesMessage(ValidationError, "'Enter a whole number.'"):
            f.clean("a")
        self.assertEqual(42, f.clean(42))
        with self.assertRaisesMessage(ValidationError, "'Enter a whole number.'"):
            f.clean(3.14)
        self.assertEqual(1, f.clean("1 "))
        self.assertEqual(1, f.clean(" 1"))
        self.assertEqual(1, f.clean(" 1 "))
        with self.assertRaisesMessage(ValidationError, "'Enter a whole number.'"):
            f.clean("1a")
        self.assertIsNone(f.max_value)
        self.assertIsNone(f.min_value)