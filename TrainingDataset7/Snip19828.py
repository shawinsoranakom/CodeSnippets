def test_validate_fields_unattached(self):
        Product.objects.create(price=42)
        constraint = models.UniqueConstraint(fields=["price"], name="uniq_prices")
        msg = "Product with this Price already exists."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(Product, Product(price=42))