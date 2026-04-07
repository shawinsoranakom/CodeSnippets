def test_validate_unique_custom_code_and_message(self):
        product = UniqueConstraintProduct.objects.create(
            name="test", color="red", age=42
        )
        code = "custom_code"
        message = "Custom message"
        multiple_fields_constraint = models.UniqueConstraint(
            fields=["color", "age"],
            name="color_age_uniq",
            violation_error_code=code,
            violation_error_message=message,
        )
        single_field_constraint = models.UniqueConstraint(
            fields=["color"],
            name="color_uniq",
            violation_error_code=code,
            violation_error_message=message,
        )

        with self.assertRaisesMessage(ValidationError, message) as cm:
            multiple_fields_constraint.validate(
                UniqueConstraintProduct,
                UniqueConstraintProduct(
                    name="new-test", color=product.color, age=product.age
                ),
            )
        self.assertEqual(cm.exception.code, code)

        with self.assertRaisesMessage(ValidationError, message) as cm:
            single_field_constraint.validate(
                UniqueConstraintProduct,
                UniqueConstraintProduct(name="new-test", color=product.color),
            )
        self.assertEqual(cm.exception.code, code)