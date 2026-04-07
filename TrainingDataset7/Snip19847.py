def test_validate_nulls_distinct_fields(self):
        Product.objects.create(price=42)
        constraint = models.UniqueConstraint(
            fields=["price"],
            nulls_distinct=False,
            name="uniq_prices_nulls_distinct",
        )
        constraint.validate(Product, Product(price=None))
        Product.objects.create(price=None)
        msg = "Product with this Price already exists."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(Product, Product(price=None))