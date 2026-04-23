def test_invalid_opclasses_argument(self):
        msg = "UniqueConstraint.opclasses must be a list or tuple."
        with self.assertRaisesMessage(TypeError, msg):
            models.UniqueConstraint(
                name="uniq_opclasses",
                fields=["field"],
                opclasses="jsonb_path_ops",
            )