def test_validate_boolean_expressions(self):
        constraint = models.CheckConstraint(
            condition=models.expressions.ExpressionWrapper(
                models.Q(price__gt=500) | models.Q(price__lt=500),
                output_field=models.BooleanField(),
            ),
            name="price_neq_500_wrap",
        )
        msg = f"Constraint “{constraint.name}” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(Product, Product(price=500, discounted_price=5))
        constraint.validate(Product, Product(price=501, discounted_price=5))
        constraint.validate(Product, Product(price=499, discounted_price=5))