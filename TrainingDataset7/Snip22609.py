def test_integerfield_5(self):
        f = IntegerField(min_value=10, max_value=20)
        self.assertWidgetRendersTo(
            f, '<input id="id_f" max="20" type="number" name="f" min="10" required>'
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
        self.assertEqual(20, f.clean(20))
        with self.assertRaisesMessage(
            ValidationError, "'Ensure this value is less than or equal to 20.'"
        ):
            f.clean(21)
        self.assertEqual(f.max_value, 20)
        self.assertEqual(f.min_value, 10)