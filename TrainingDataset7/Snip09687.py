def supports_comparing_boolean_expr(self):
        return self.connection.oracle_version >= (23,)