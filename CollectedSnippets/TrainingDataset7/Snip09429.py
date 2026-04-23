def _delete_primary_key_sql(self, model, name):
        return self._delete_constraint_sql(self.sql_delete_pk, model, name)