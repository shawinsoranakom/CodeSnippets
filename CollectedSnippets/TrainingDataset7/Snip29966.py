def test_integer_open(self):
        field = pg_forms.IntegerRangeField()
        value = field.clean(["", "0"])
        self.assertEqual(value, NumericRange(None, 0))