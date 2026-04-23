def test_disallowed(self):
        class Max(Func):
            function = "MAX"

        tests = [
            Expression(),
            F("field"),
            Max(F("count"), 1),
            Value(10) + F("count"),  # Combined expression.
            ExpressionList(F("count"), Value(2)),
            ExpressionWrapper(F("count"), output_field=FloatField()),
            Collate(Value("John"), "nocase"),
            OrderByList("field"),
        ]
        for expression in tests:
            with self.subTest(expression=expression):
                self.assertIs(expression.allowed_default, False)