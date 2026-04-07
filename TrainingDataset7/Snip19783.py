def test_validate(self):
        check = models.Q(price__gt=models.F("discounted_price"))
        constraint = models.CheckConstraint(condition=check, name="price")
        # Invalid product.
        invalid_product = Product(price=10, discounted_price=42)
        with self.assertRaises(ValidationError):
            constraint.validate(Product, invalid_product)
        with self.assertRaises(ValidationError):
            constraint.validate(Product, invalid_product, exclude={"unit"})
        # Fields used by the check constraint are excluded.
        constraint.validate(Product, invalid_product, exclude={"price"})
        constraint.validate(Product, invalid_product, exclude={"discounted_price"})
        constraint.validate(
            Product,
            invalid_product,
            exclude={"discounted_price", "price"},
        )
        # Valid product.
        constraint.validate(Product, Product(price=10, discounted_price=5))