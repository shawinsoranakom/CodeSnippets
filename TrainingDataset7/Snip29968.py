def test_integer_invalid_lower(self):
        field = pg_forms.IntegerRangeField()
        msg = "Enter a whole number."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean(["a", "2"])