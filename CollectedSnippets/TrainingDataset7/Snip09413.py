def _delete_fk_sql(self, model, name):
        return self._delete_constraint_sql(self.sql_delete_fk, model, name)