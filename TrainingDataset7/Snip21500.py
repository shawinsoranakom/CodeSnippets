def test_output_field_or_none_property_not_cached(self):
        expression = Value(None, output_field=None)
        self.assertIsNone(expression._output_field_or_none)
        expression.output_field = BooleanField()
        self.assertIsInstance(expression._output_field_or_none, BooleanField)