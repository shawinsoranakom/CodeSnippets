def remove_sql(self, model, schema_editor, **kwargs):
                kwargs.setdefault("sql", self.sql_delete_index)
                return super().remove_sql(model, schema_editor, **kwargs)