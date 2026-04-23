def test_resolve_output_field_positive_integer(self):
        connectors = [
            Combinable.ADD,
            Combinable.MUL,
            Combinable.DIV,
            Combinable.MOD,
            Combinable.POW,
        ]
        for connector in connectors:
            with self.subTest(connector=connector):
                expr = CombinedExpression(
                    Expression(PositiveIntegerField()),
                    connector,
                    Expression(PositiveIntegerField()),
                )
                self.assertIsInstance(expr.output_field, PositiveIntegerField)