def test_custom_suffix(self):
        class CustomSuffixIndex(PostgresIndex):
            suffix = "sfx"

            def create_sql(self, model, schema_editor, using="gin", **kwargs):
                return super().create_sql(model, schema_editor, using=using, **kwargs)

        index = CustomSuffixIndex(fields=["field"], name="custom_suffix_idx")
        self.assertEqual(index.suffix, "sfx")
        with connection.schema_editor() as editor:
            self.assertIn(
                " USING gin ",
                str(index.create_sql(CharFieldModel, editor)),
            )