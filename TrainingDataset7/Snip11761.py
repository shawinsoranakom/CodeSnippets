def remove_sql(self, model, schema_editor, **kwargs):
        return schema_editor._delete_index_sql(model, self.name, **kwargs)