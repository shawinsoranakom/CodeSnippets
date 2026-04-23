def test_requires_name(self):
        msg = "A unique constraint must be named."
        with self.assertRaisesMessage(ValueError, msg):
            models.UniqueConstraint(fields=["field"], name="")