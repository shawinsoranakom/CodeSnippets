def test_validate_condition_custom_error(self):
        p1 = UniqueConstraintConditionProduct.objects.create(name="p1")
        constraint = models.UniqueConstraint(
            fields=["name"],
            name="name_without_color_uniq",
            condition=models.Q(color__isnull=True),
            violation_error_code="custom_code",
            violation_error_message="Custom message",
        )
        msg = "Custom message"
        with self.assertRaisesMessage(ValidationError, msg) as cm:
            constraint.validate(
                UniqueConstraintConditionProduct,
                UniqueConstraintConditionProduct(name=p1.name, color=None),
            )
        self.assertEqual(cm.exception.code, "custom_code")