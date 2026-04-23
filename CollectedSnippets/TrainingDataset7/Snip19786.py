def test_validate_rawsql_expressions_noop(self):
        constraint = models.CheckConstraint(
            condition=models.expressions.RawSQL(
                "price < %s OR price > %s",
                (500, 500),
                output_field=models.BooleanField(),
            ),
            name="price_neq_500_raw",
        )
        # RawSQL can not be checked and is always considered valid.
        constraint.validate(Product, Product(price=500, discounted_price=5))
        constraint.validate(Product, Product(price=501, discounted_price=5))
        constraint.validate(Product, Product(price=499, discounted_price=5))