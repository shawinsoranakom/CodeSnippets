def test_floatfield_3(self):
        f = FloatField(max_value=1.5, min_value=0.5)
        self.assertWidgetRendersTo(
            f,
            '<input step="any" name="f" min="0.5" max="1.5" type="number" id="id_f" '
            "required>",
        )
        with self.assertRaisesMessage(
            ValidationError, "'Ensure this value is less than or equal to 1.5.'"
        ):
            f.clean("1.6")
        with self.assertRaisesMessage(
            ValidationError, "'Ensure this value is greater than or equal to 0.5.'"
        ):
            f.clean("0.4")
        self.assertEqual(1.5, f.clean("1.5"))
        self.assertEqual(0.5, f.clean("0.5"))
        self.assertEqual(f.max_value, 1.5)
        self.assertEqual(f.min_value, 0.5)