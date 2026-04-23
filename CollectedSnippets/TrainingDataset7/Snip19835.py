def test_validate_expression_condition(self):
        constraint = models.UniqueConstraint(
            Lower("name"),
            name="name_lower_without_color_uniq",
            condition=models.Q(color__isnull=True),
        )
        non_unique_product = UniqueConstraintProduct(name=self.p2.name.upper())
        msg = "Constraint “name_lower_without_color_uniq” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(UniqueConstraintProduct, non_unique_product)
        # Values not matching condition are ignored.
        constraint.validate(
            UniqueConstraintProduct,
            UniqueConstraintProduct(name=self.p1.name, color=self.p1.color),
        )
        # Existing instances have their existing row excluded.
        constraint.validate(UniqueConstraintProduct, self.p2)
        # Unique field is excluded.
        constraint.validate(
            UniqueConstraintProduct,
            non_unique_product,
            exclude={"name"},
        )
        # Field from a condition is excluded.
        constraint.validate(
            UniqueConstraintProduct,
            non_unique_product,
            exclude={"color"},
        )