def test_non_empty_group_by(self):
        value = Value("f")
        value.output_field = None
        expr = ExpressionWrapper(Lower(value), output_field=IntegerField())
        group_by_cols = expr.get_group_by_cols()
        self.assertEqual(group_by_cols, [expr.expression])
        self.assertEqual(group_by_cols[0].output_field, expr.output_field)