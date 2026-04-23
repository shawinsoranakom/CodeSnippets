def remove_sql(self, model, schema_editor):
        return schema_editor._delete_constraint_sql(
            schema_editor.sql_delete_check,
            model,
            schema_editor.quote_name(self.name),
        )