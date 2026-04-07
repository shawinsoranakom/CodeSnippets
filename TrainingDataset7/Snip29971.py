def test_decimal_lower_bound_higher(self):
        field = pg_forms.DecimalRangeField()
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean(["1.8", "1.6"])
        self.assertEqual(
            cm.exception.messages[0],
            "The start of the range must not exceed the end of the range.",
        )
        self.assertEqual(cm.exception.code, "bound_ordering")