def test_validate_nullable_field_with_isnull(self):
        constraint = models.CheckConstraint(
            condition=models.Q(price__gte=0) | models.Q(price__isnull=True),
            name="positive_price",
        )
        constraint.validate(Product, Product())