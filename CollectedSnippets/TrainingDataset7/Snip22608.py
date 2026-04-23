def test_integerfield_4(self):
        f = IntegerField(min_value=10)
        self.assertWidgetRendersTo(
            f, '<input id="id_f" type="number" name="f" min="10" required>'
        )
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(None)
        with self.assertRaisesMessage(
            ValidationError, "'Ensure this value is greater than or equal to 10.'"
        ):
            f.clean(1)
        self.assertEqual(10, f.clean(10))
        self.assertEqual(11, f.clean(11))
        self.assertEqual(10, f.clean("10"))
        self.assertEqual(11, f.clean("11"))
        self.assertIsNone(f.max_value)
        self.assertEqual(f.min_value, 10)