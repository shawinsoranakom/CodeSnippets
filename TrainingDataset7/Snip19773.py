def test_eq(self):
        check1 = models.Q(price__gt=models.F("discounted_price"))
        check2 = models.Q(price__lt=models.F("discounted_price"))
        self.assertEqual(
            models.CheckConstraint(condition=check1, name="price"),
            models.CheckConstraint(condition=check1, name="price"),
        )
        self.assertEqual(
            models.CheckConstraint(condition=check1, name="price"), mock.ANY
        )
        self.assertNotEqual(
            models.CheckConstraint(condition=check1, name="price"),
            models.CheckConstraint(condition=check1, name="price2"),
        )
        self.assertNotEqual(
            models.CheckConstraint(condition=check1, name="price"),
            models.CheckConstraint(condition=check2, name="price"),
        )
        self.assertNotEqual(models.CheckConstraint(condition=check1, name="price"), 1)
        self.assertNotEqual(
            models.CheckConstraint(condition=check1, name="price"),
            models.CheckConstraint(
                condition=check1, name="price", violation_error_message="custom error"
            ),
        )
        self.assertNotEqual(
            models.CheckConstraint(
                condition=check1, name="price", violation_error_message="custom error"
            ),
            models.CheckConstraint(
                condition=check1,
                name="price",
                violation_error_message="other custom error",
            ),
        )
        self.assertEqual(
            models.CheckConstraint(
                condition=check1, name="price", violation_error_message="custom error"
            ),
            models.CheckConstraint(
                condition=check1, name="price", violation_error_message="custom error"
            ),
        )
        self.assertNotEqual(
            models.CheckConstraint(condition=check1, name="price"),
            models.CheckConstraint(
                condition=check1, name="price", violation_error_code="custom_code"
            ),
        )
        self.assertEqual(
            models.CheckConstraint(
                condition=check1, name="price", violation_error_code="custom_code"
            ),
            models.CheckConstraint(
                condition=check1, name="price", violation_error_code="custom_code"
            ),
        )