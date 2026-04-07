def supports_boolean_expr_in_select_clause(self):
        return self.connection.oracle_version >= (23,)