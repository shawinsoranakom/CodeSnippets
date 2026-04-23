def test_deferrable_with_opclasses(self):
        message = "UniqueConstraint with opclasses cannot be deferred."
        with self.assertRaisesMessage(ValueError, message):
            models.UniqueConstraint(
                fields=["name"],
                name="name_text_pattern_ops_unique",
                opclasses=["text_pattern_ops"],
                deferrable=models.Deferrable.DEFERRED,
            )