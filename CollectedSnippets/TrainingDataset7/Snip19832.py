def test_validate_field_transform(self):
        updated_date = datetime(2005, 7, 26)
        UniqueConstraintProduct.objects.create(name="p1", updated=updated_date)
        constraint = models.UniqueConstraint(
            models.F("updated__date"), name="date_created_unique"
        )
        msg = "Constraint “date_created_unique” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(
                UniqueConstraintProduct,
                UniqueConstraintProduct(updated=updated_date),
            )
        constraint.validate(
            UniqueConstraintProduct,
            UniqueConstraintProduct(updated=updated_date + timedelta(days=1)),
        )