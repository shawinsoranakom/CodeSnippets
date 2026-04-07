def test_floatfield_1(self):
        f = FloatField()
        self.assertWidgetRendersTo(
            f, '<input step="any" type="number" name="f" id="id_f" required>'
        )
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean("")
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(None)
        self.assertEqual(1.0, f.clean("1"))
        self.assertIsInstance(f.clean("1"), float)
        self.assertEqual(23.0, f.clean("23"))
        self.assertEqual(3.1400000000000001, f.clean("3.14"))
        self.assertEqual(3.1400000000000001, f.clean(3.14))
        self.assertEqual(42.0, f.clean(42))
        with self.assertRaisesMessage(ValidationError, "'Enter a number.'"):
            f.clean("a")
        self.assertEqual(1.0, f.clean("1.0 "))
        self.assertEqual(1.0, f.clean(" 1.0"))
        self.assertEqual(1.0, f.clean(" 1.0 "))
        with self.assertRaisesMessage(ValidationError, "'Enter a number.'"):
            f.clean("1.0a")
        self.assertIsNone(f.max_value)
        self.assertIsNone(f.min_value)
        with self.assertRaisesMessage(ValidationError, "'Enter a number.'"):
            f.clean("Infinity")
        with self.assertRaisesMessage(ValidationError, "'Enter a number.'"):
            f.clean("NaN")
        with self.assertRaisesMessage(ValidationError, "'Enter a number.'"):
            f.clean("-Inf")