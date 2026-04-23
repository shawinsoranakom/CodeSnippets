def test_expressions_and_fields_mutually_exclusive(self):
        msg = "UniqueConstraint.fields and expressions are mutually exclusive."
        with self.assertRaisesMessage(ValueError, msg):
            models.UniqueConstraint(Lower("field_1"), fields=["field_2"], name="name")