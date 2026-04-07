def test_validate(self):
        constraint = UniqueConstraintProduct._meta.constraints[0]
        msg = "Unique constraint product with this Name and Color already exists."
        non_unique_product = UniqueConstraintProduct(
            name=self.p1.name, color=self.p1.color
        )
        with self.assertRaisesMessage(ValidationError, msg) as cm:
            constraint.validate(UniqueConstraintProduct, non_unique_product)
        self.assertEqual(cm.exception.code, "unique_together")
        # Null values are ignored.
        constraint.validate(
            UniqueConstraintProduct,
            UniqueConstraintProduct(name=self.p2.name, color=None),
        )
        # Existing instances have their existing row excluded.
        constraint.validate(UniqueConstraintProduct, self.p1)
        # Unique fields are excluded.
        constraint.validate(
            UniqueConstraintProduct,
            non_unique_product,
            exclude={"name"},
        )
        constraint.validate(
            UniqueConstraintProduct,
            non_unique_product,
            exclude={"color"},
        )
        constraint.validate(
            UniqueConstraintProduct,
            non_unique_product,
            exclude={"name", "color"},
        )
        # Validation on a child instance.
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(
                UniqueConstraintProduct,
                ChildUniqueConstraintProduct(name=self.p1.name, color=self.p1.color),
            )