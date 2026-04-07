def test_decimalfield_3(self):
        f = DecimalField(
            max_digits=4,
            decimal_places=2,
            max_value=decimal.Decimal("1.5"),
            min_value=decimal.Decimal("0.5"),
        )
        self.assertWidgetRendersTo(
            f,
            '<input step="0.01" name="f" min="0.5" max="1.5" type="number" id="id_f" '
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
        self.assertEqual(f.clean("1.5"), decimal.Decimal("1.5"))
        self.assertEqual(f.clean("0.5"), decimal.Decimal("0.5"))
        self.assertEqual(f.clean(".5"), decimal.Decimal("0.5"))
        self.assertEqual(f.clean("00.50"), decimal.Decimal("0.50"))
        self.assertEqual(f.max_digits, 4)
        self.assertEqual(f.decimal_places, 2)
        self.assertEqual(f.max_value, decimal.Decimal("1.5"))
        self.assertEqual(f.min_value, decimal.Decimal("0.5"))