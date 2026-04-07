def assertGeneratedFieldWithExpressionIsValidated(self, model):
        constraint = UniqueConstraint(Sqrt("rebate"), name="unique_rebate_sqrt")
        model.objects.create(price=100, discounted_price=84)

        valid_product = model(price=100, discounted_price=75)
        constraint.validate(model, valid_product)

        invalid_product = model(price=20, discounted_price=4)
        with self.assertRaisesMessage(
            ValidationError, f"Constraint “{constraint.name}” is violated."
        ):
            constraint.validate(model, invalid_product)

        # Excluding referenced or generated fields should skip validation.
        constraint.validate(model, invalid_product, exclude={"rebate"})
        constraint.validate(model, invalid_product, exclude={"price"})