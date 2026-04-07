def test_requires_field_or_expression(self):
        msg = "At least one field or expression is required to define an index."
        with self.assertRaisesMessage(ValueError, msg):
            models.Index()