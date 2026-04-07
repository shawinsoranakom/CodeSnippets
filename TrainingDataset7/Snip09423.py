def _delete_check_sql(self, model, name):
        if not self.connection.features.supports_table_check_constraints:
            return None
        return self._delete_constraint_sql(self.sql_delete_check, model, name)