def test_resolve_output_field_numbers_with_null(self):
        test_values = [
            (3.14159, None, FloatField),
            (None, 3.14159, FloatField),
            (None, 42, IntegerField),
            (42, None, IntegerField),
            (None, Decimal("3.14"), DecimalField),
            (Decimal("3.14"), None, DecimalField),
        ]
        connectors = [
            Combinable.ADD,
            Combinable.SUB,
            Combinable.MUL,
            Combinable.DIV,
            Combinable.MOD,
            Combinable.POW,
        ]
        for lhs, rhs, expected_output_field in test_values:
            for connector in connectors:
                with self.subTest(lhs=lhs, connector=connector, rhs=rhs):
                    expr = CombinedExpression(Value(lhs), connector, Value(rhs))
                    self.assertIsInstance(expr.output_field, expected_output_field)