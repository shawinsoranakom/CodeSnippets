def test_resolve_output_field_dates(self):
        tests = [
            # Add - same type.
            (DateField, Combinable.ADD, DateField, FieldError),
            (DateTimeField, Combinable.ADD, DateTimeField, FieldError),
            (TimeField, Combinable.ADD, TimeField, FieldError),
            (DurationField, Combinable.ADD, DurationField, DurationField),
            # Add - different type.
            (DateField, Combinable.ADD, DurationField, DateTimeField),
            (DateTimeField, Combinable.ADD, DurationField, DateTimeField),
            (TimeField, Combinable.ADD, DurationField, TimeField),
            (DurationField, Combinable.ADD, DateField, DateTimeField),
            (DurationField, Combinable.ADD, DateTimeField, DateTimeField),
            (DurationField, Combinable.ADD, TimeField, TimeField),
            # Subtract - same type.
            (DateField, Combinable.SUB, DateField, DurationField),
            (DateTimeField, Combinable.SUB, DateTimeField, DurationField),
            (TimeField, Combinable.SUB, TimeField, DurationField),
            (DurationField, Combinable.SUB, DurationField, DurationField),
            # Subtract - different type.
            (DateField, Combinable.SUB, DurationField, DateTimeField),
            (DateTimeField, Combinable.SUB, DurationField, DateTimeField),
            (TimeField, Combinable.SUB, DurationField, TimeField),
            (DurationField, Combinable.SUB, DateField, FieldError),
            (DurationField, Combinable.SUB, DateTimeField, FieldError),
            (DurationField, Combinable.SUB, DateTimeField, FieldError),
        ]
        for lhs, connector, rhs, combined in tests:
            msg = (
                f"Cannot infer type of {connector!r} expression involving these types: "
            )
            with self.subTest(lhs=lhs, connector=connector, rhs=rhs, combined=combined):
                expr = CombinedExpression(
                    Expression(lhs()),
                    connector,
                    Expression(rhs()),
                )
                if issubclass(combined, Exception):
                    with self.assertRaisesMessage(combined, msg):
                        expr.output_field
                else:
                    self.assertIsInstance(expr.output_field, combined)