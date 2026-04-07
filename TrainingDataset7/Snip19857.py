def test_invalid_defer_argument(self):
        message = "UniqueConstraint.deferrable must be a Deferrable instance."
        with self.assertRaisesMessage(TypeError, message):
            models.UniqueConstraint(
                fields=["name"],
                name="name_invalid",
                deferrable="invalid",
            )