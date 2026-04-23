def _field_db_check(self, field, field_db_params):
        # Always check constraints with the same mocked column name to avoid
        # recreating constraints when the column is renamed.
        check_constraints = self.connection.data_type_check_constraints
        data = field.db_type_parameters(self.connection)
        data["column"] = "__column_name__"
        try:
            return check_constraints[field.get_internal_type()] % data
        except KeyError:
            return None