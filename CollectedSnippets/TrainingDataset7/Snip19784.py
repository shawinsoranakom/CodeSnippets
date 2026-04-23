def test_validate_custom_error(self):
        check = models.Q(price__gt=models.F("discounted_price"))
        constraint = models.CheckConstraint(
            condition=check,
            name="price",
            violation_error_message="discount is fake",
            violation_error_code="fake_discount",
        )
        # Invalid product.
        invalid_product = Product(price=10, discounted_price=42)
        msg = "discount is fake"
        with self.assertRaisesMessage(ValidationError, msg) as cm:
            constraint.validate(Product, invalid_product)
        self.assertEqual(cm.exception.code, "fake_discount")