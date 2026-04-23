def test_empty_group_by(self):
        expr = ExpressionWrapper(Value(3), output_field=IntegerField())
        self.assertEqual(expr.get_group_by_cols(), [])