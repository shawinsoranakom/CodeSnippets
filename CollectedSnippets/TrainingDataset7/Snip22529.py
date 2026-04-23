def test_decimalfield_1(self):
        f = DecimalField(max_digits=4, decimal_places=2)
        self.assertWidgetRendersTo(
            f, '<input id="id_f" step="0.01" type="number" name="f" required>'
        )
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean("")
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(None)
        self.assertEqual(f.clean("1"), decimal.Decimal("1"))
        self.assertIsInstance(f.clean("1"), decimal.Decimal)
        self.assertEqual(f.clean("23"), decimal.Decimal("23"))
        self.assertEqual(f.clean("3.14"), decimal.Decimal("3.14"))
        self.assertEqual(f.clean(3.14), decimal.Decimal("3.14"))
        self.assertEqual(f.clean(decimal.Decimal("3.14")), decimal.Decimal("3.14"))
        self.assertEqual(f.clean("1.0 "), decimal.Decimal("1.0"))
        self.assertEqual(f.clean(" 1.0"), decimal.Decimal("1.0"))
        self.assertEqual(f.clean(" 1.0 "), decimal.Decimal("1.0"))
        with self.assertRaisesMessage(
            ValidationError, "'Ensure that there are no more than 4 digits in total.'"
        ):
            f.clean("123.45")
        with self.assertRaisesMessage(
            ValidationError, "'Ensure that there are no more than 2 decimal places.'"
        ):
            f.clean("1.234")
        msg = "'Ensure that there are no more than 2 digits before the decimal point.'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("123.4")
        self.assertEqual(f.clean("-12.34"), decimal.Decimal("-12.34"))
        with self.assertRaisesMessage(
            ValidationError, "'Ensure that there are no more than 4 digits in total.'"
        ):
            f.clean("-123.45")
        self.assertEqual(f.clean("-.12"), decimal.Decimal("-0.12"))
        self.assertEqual(f.clean("-00.12"), decimal.Decimal("-0.12"))
        self.assertEqual(f.clean("-000.12"), decimal.Decimal("-0.12"))
        with self.assertRaisesMessage(
            ValidationError, "'Ensure that there are no more than 2 decimal places.'"
        ):
            f.clean("-000.123")
        with self.assertRaisesMessage(
            ValidationError, "'Ensure that there are no more than 4 digits in total.'"
        ):
            f.clean("-000.12345")
        self.assertEqual(f.max_digits, 4)
        self.assertEqual(f.decimal_places, 2)
        self.assertIsNone(f.max_value)
        self.assertIsNone(f.min_value)