def test_decimalfield_step_size_min_value(self):
        f = DecimalField(
            step_size=decimal.Decimal("0.3"),
            min_value=decimal.Decimal("-0.4"),
        )
        self.assertWidgetRendersTo(
            f,
            '<input name="f" min="-0.4" step="0.3" type="number" id="id_f" required>',
        )
        msg = (
            "Ensure this value is a multiple of step size 0.3, starting from -0.4, "
            "e.g. -0.4, -0.1, 0.2, and so on."
        )
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("1")
        self.assertEqual(f.clean("0.2"), decimal.Decimal("0.2"))
        self.assertEqual(f.clean(2), decimal.Decimal(2))
        self.assertEqual(f.step_size, decimal.Decimal("0.3"))