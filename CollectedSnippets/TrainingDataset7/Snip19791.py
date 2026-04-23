def test_validate_fk_attname(self):
        constraint_with_fk = models.CheckConstraint(
            condition=models.Q(uniqueconstraintproduct_ptr_id__isnull=False),
            name="parent_ptr_present",
        )
        with self.assertRaisesMessage(
            ValidationError, "Constraint “parent_ptr_present” is violated."
        ):
            constraint_with_fk.validate(
                ChildUniqueConstraintProduct, ChildUniqueConstraintProduct()
            )
        constraint_with_fk.validate(
            ChildUniqueConstraintProduct,
            ChildUniqueConstraintProduct(uniqueconstraintproduct_ptr_id=1),
        )