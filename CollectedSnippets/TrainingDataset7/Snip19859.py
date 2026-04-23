def test_invalid_include_argument(self):
        msg = "UniqueConstraint.include must be a list or tuple."
        with self.assertRaisesMessage(TypeError, msg):
            models.UniqueConstraint(
                name="uniq_include",
                fields=["field"],
                include="other",
            )