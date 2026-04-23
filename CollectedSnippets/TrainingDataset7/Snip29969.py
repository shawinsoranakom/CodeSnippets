def test_integer_invalid_upper(self):
        field = pg_forms.IntegerRangeField()
        msg = "Enter a whole number."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean(["1", "b"])