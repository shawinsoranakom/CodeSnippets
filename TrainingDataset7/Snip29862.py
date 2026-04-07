def test_custom_sql(self):
        class CustomSQLIndex(PostgresIndex):
            sql_create_index = "SELECT 1"
            sql_delete_index = "SELECT 2"

            def create_sql(self, model, schema_editor, using="", **kwargs):
                kwargs.setdefault("sql", self.sql_create_index)
                return super().create_sql(model, schema_editor, using, **kwargs)

            def remove_sql(self, model, schema_editor, **kwargs):
                kwargs.setdefault("sql", self.sql_delete_index)
                return super().remove_sql(model, schema_editor, **kwargs)

        index = CustomSQLIndex(fields=["field"], name="custom_sql_idx")

        operations = [
            (index.create_sql, CustomSQLIndex.sql_create_index),
            (index.remove_sql, CustomSQLIndex.sql_delete_index),
        ]
        for operation, expected in operations:
            with self.subTest(operation=operation.__name__):
                with connection.schema_editor() as editor:
                    self.assertEqual(expected, str(operation(CharFieldModel, editor)))