def assertGeneratedFieldWithFieldsIsValidated(self, model):
        constraint = models.UniqueConstraint(
            fields=["lower_name"], name="lower_name_unique"
        )
        model.objects.create(name="Box")
        constraint.validate(model, model(name="Case"))

        invalid_product = model(name="BOX")
        msg = str(invalid_product.unique_error_message(model, ["lower_name"]))
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(model, invalid_product)

        # Excluding referenced or generated fields should skip validation.
        constraint.validate(model, invalid_product, exclude={"lower_name"})
        constraint.validate(model, invalid_product, exclude={"name"})