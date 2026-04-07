def create_sql(self, model, schema_editor, using="", **kwargs):
                kwargs.setdefault("sql", self.sql_create_index)
                return super().create_sql(model, schema_editor, using, **kwargs)