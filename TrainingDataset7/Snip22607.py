def test_integerfield_3(self):
        f = IntegerField(max_value=10)
        self.assertWidgetRendersTo(
            f, '<input max="10" type="number" name="f" id="id_f" required>'
        )
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(None)
        self.assertEqual(1, f.clean(1))
        self.assertEqual(10, f.clean(10))
        with self.assertRaisesMessage(
            ValidationError, "'Ensure this value is less than or equal to 10.'"
        ):
            f.clean(11)
        self.assertEqual(10, f.clean("10"))
        with self.assertRaisesMessage(
            ValidationError, "'Ensure this value is less than or equal to 10.'"
        ):
            f.clean("11")
        self.assertEqual(f.max_value, 10)
        self.assertIsNone(f.min_value)