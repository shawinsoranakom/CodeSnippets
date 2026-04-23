def test_validate_case_when(self):
        UniqueConstraintProduct.objects.create(name="p1")
        constraint = models.UniqueConstraint(
            Case(When(color__isnull=True, then=F("name"))),
            name="name_without_color_uniq",
        )
        msg = "Constraint “name_without_color_uniq” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(
                UniqueConstraintProduct,
                UniqueConstraintProduct(name="p1"),
            )
        constraint.validate(
            UniqueConstraintProduct,
            UniqueConstraintProduct(name="p1", color="green"),
        )