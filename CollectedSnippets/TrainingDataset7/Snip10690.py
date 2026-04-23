def constraint_sql(self, model, schema_editor):
        check = self._get_check_sql(model, schema_editor)
        return schema_editor._check_sql(self.name, check)