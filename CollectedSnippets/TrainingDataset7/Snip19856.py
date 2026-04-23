def test_deferrable_with_expressions(self):
        message = "UniqueConstraint with expressions cannot be deferred."
        with self.assertRaisesMessage(ValueError, message):
            models.UniqueConstraint(
                Lower("name"),
                name="deferred_expression_unique",
                deferrable=models.Deferrable.DEFERRED,
            )