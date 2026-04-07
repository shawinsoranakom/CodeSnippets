def test_decimal_required(self):
        field = pg_forms.DecimalRangeField(required=True)
        msg = "This field is required."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean(["", ""])
        value = field.clean(["1.61803399", ""])
        self.assertEqual(value, NumericRange(Decimal("1.61803399"), None))