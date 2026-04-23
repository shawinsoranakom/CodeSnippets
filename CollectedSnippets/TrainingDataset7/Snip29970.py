def test_integer_required(self):
        field = pg_forms.IntegerRangeField(required=True)
        msg = "This field is required."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean(["", ""])
        value = field.clean([1, ""])
        self.assertEqual(value, NumericRange(1, None))