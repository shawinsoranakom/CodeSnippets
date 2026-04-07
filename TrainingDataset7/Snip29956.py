def test_valid_integer(self):
        field = pg_forms.IntegerRangeField()
        value = field.clean(["1", "2"])
        self.assertEqual(value, NumericRange(1, 2))