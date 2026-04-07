def test_validate_ordered_expression(self):
        constraint = models.UniqueConstraint(
            Lower("name").desc(), name="name_lower_uniq_desc"
        )
        msg = "Constraint “name_lower_uniq_desc” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(
                UniqueConstraintProduct,
                UniqueConstraintProduct(name=self.p1.name.upper()),
            )
        constraint.validate(
            UniqueConstraintProduct,
            UniqueConstraintProduct(name="another-name"),
        )
        # Existing instances have their existing row excluded.
        constraint.validate(UniqueConstraintProduct, self.p1)
        # Unique field is excluded.
        constraint.validate(
            UniqueConstraintProduct,
            UniqueConstraintProduct(name=self.p1.name.upper()),
            exclude={"name"},
        )