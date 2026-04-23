def test_none(self):
        field = pg_forms.IntegerRangeField(required=False)
        value = field.clean(["", ""])
        self.assertIsNone(value)