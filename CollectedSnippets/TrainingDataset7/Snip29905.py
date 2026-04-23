def test_deconstruct(self):
        field = pg_fields.DecimalRangeField()
        *_, kwargs = field.deconstruct()
        self.assertEqual(kwargs, {})
        field = pg_fields.DecimalRangeField(default_bounds="[]")
        *_, kwargs = field.deconstruct()
        self.assertEqual(kwargs, {"default_bounds": "[]"})