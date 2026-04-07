def remove_sql(self, model, schema_editor):
        return schema_editor._delete_check_sql(model, self.name)