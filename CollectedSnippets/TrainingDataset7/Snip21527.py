def test_resolve_output_field_with_null(self):
        def null():
            return Value(None)

        tests = [
            # Numbers.
            (AutoField, Combinable.ADD, null),
            (DecimalField, Combinable.ADD, null),
            (FloatField, Combinable.ADD, null),
            (IntegerField, Combinable.ADD, null),
            (IntegerField, Combinable.SUB, null),
            (null, Combinable.ADD, IntegerField),
            # Dates.
            (DateField, Combinable.ADD, null),
            (DateTimeField, Combinable.ADD, null),
            (DurationField, Combinable.ADD, null),
            (TimeField, Combinable.ADD, null),
            (TimeField, Combinable.SUB, null),
            (null, Combinable.ADD, DateTimeField),
            (DateField, Combinable.SUB, null),
        ]
        for lhs, connector, rhs in tests:
            msg = (
                f"Cannot infer type of {connector!r} expression involving these types: "
            )
            with self.subTest(lhs=lhs, connector=connector, rhs=rhs):
                expr = CombinedExpression(
                    Expression(lhs()),
                    connector,
                    Expression(rhs()),
                )
                with self.assertRaisesMessage(FieldError, msg):
                    expr.output_field