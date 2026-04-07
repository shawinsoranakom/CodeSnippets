def test_requires_field_or_expression(self):
        msg = (
            "At least one field or expression is required to define a unique "
            "constraint."
        )
        with self.assertRaisesMessage(ValueError, msg):
            models.UniqueConstraint(name="name")