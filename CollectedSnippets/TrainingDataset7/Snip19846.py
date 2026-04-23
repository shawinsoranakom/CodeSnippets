def test_validate_nullable_textfield_with_isnull_true(self):
        is_null_constraint = models.UniqueConstraint(
            "price",
            "discounted_price",
            condition=models.Q(unit__isnull=True),
            name="uniq_prices_no_unit",
        )
        is_not_null_constraint = models.UniqueConstraint(
            "price",
            "discounted_price",
            condition=models.Q(unit__isnull=False),
            name="uniq_prices_unit",
        )

        Product.objects.create(price=2, discounted_price=1)
        Product.objects.create(price=4, discounted_price=3, unit="ng/mL")

        msg = "Constraint “uniq_prices_no_unit” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            is_null_constraint.validate(
                Product, Product(price=2, discounted_price=1, unit=None)
            )
        is_null_constraint.validate(
            Product, Product(price=2, discounted_price=1, unit="ng/mL")
        )
        is_null_constraint.validate(Product, Product(price=4, discounted_price=3))

        msg = "Constraint “uniq_prices_unit” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            is_not_null_constraint.validate(
                Product,
                Product(price=4, discounted_price=3, unit="μg/mL"),
            )
        is_not_null_constraint.validate(Product, Product(price=4, discounted_price=3))
        is_not_null_constraint.validate(Product, Product(price=2, discounted_price=1))