def test_model_validation_constraint_no_code_error(self):
        class ValidateNoCodeErrorConstraint(UniqueConstraint):
            def validate(self, model, instance, **kwargs):
                raise ValidationError({"name": ValidationError("Already exists.")})

        class NoCodeErrorConstraintModel(models.Model):
            name = models.CharField(max_length=255)

            class Meta:
                constraints = [
                    ValidateNoCodeErrorConstraint(
                        Lower("name"),
                        name="custom_validate_no_code_error",
                    )
                ]

        msg = "{'name': ['Already exists.']}"
        with self.assertRaisesMessage(ValidationError, msg):
            NoCodeErrorConstraintModel(name="test").validate_constraints()