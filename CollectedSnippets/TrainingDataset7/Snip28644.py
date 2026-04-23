def test_expressions_with_opclasses(self):
        msg = (
            "Index.opclasses cannot be used with expressions. Use "
            "django.contrib.postgres.indexes.OpClass() instead."
        )
        with self.assertRaisesMessage(ValueError, msg):
            models.Index(
                Lower("field"),
                name="test_func_opclass",
                opclasses=["jsonb_path_ops"],
            )