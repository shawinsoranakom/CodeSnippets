def assertGeneratedFieldNullsDistinctIsValidated(self, model):
        constraint = models.UniqueConstraint(
            fields=["lower_name"],
            name="lower_name_unique_nulls_distinct",
            nulls_distinct=False,
        )
        model.objects.create(name=None)
        valid_product = model(name="Box")
        constraint.validate(model, valid_product)

        invalid_product = model(name=None)
        msg = str(invalid_product.unique_error_message(model, ["lower_name"]))
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(model, invalid_product)