def assertGeneratedFieldIsValidated(self, model):
        constraint = models.CheckConstraint(
            condition=models.Q(rebate__range=(0, 100)), name="bounded_rebate"
        )
        constraint.validate(model, model(price=50, discounted_price=20))

        invalid_product = model(price=1200, discounted_price=500)
        msg = f"Constraint “{constraint.name}” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(model, invalid_product)

        # Excluding referenced or generated fields should skip validation.
        constraint.validate(model, invalid_product, exclude={"price"})
        constraint.validate(model, invalid_product, exclude={"rebate"})