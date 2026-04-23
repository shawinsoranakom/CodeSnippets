def on_delete_sql(self, schema_editor):
        return schema_editor.connection.ops.fk_on_delete_sql(self.operation)