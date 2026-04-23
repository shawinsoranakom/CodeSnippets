def get_placeholder_sql(self, value, compiler, connection):
        return connection.ops.binary_placeholder_sql(value, compiler)