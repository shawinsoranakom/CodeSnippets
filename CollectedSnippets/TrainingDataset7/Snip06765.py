def get_placeholder_sql(self, value, compiler, connection):
        """
        Return the placeholder for the spatial column for the
        given value.
        """
        return connection.ops.get_geom_placeholder_sql(self, value, compiler)