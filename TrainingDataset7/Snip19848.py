def test_validate_nulls_distinct_expressions(self):
        Product.objects.create(price=42)
        constraint = models.UniqueConstraint(
            Abs("price"),
            nulls_distinct=False,
            name="uniq_prices_nulls_distinct",
        )
        constraint.validate(Product, Product(price=None))
        Product.objects.create(price=None)
        msg = f"Constraint “{constraint.name}” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(Product, Product(price=None))