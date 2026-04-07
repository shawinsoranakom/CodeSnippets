def test_validate_nullable_field_with_none(self):
        # Nullable fields should be considered valid on None values.
        constraint = models.CheckConstraint(
            condition=models.Q(price__gte=0),
            name="positive_price",
        )
        constraint.validate(Product, Product())