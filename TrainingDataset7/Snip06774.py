def select_format(self, compiler, sql, params):
        """
        Return the selection format string, depending on the requirements
        of the spatial backend. For example, Oracle and MySQL require custom
        selection formats in order to retrieve geometries in OGC WKB.
        """
        if not compiler.query.subquery:
            return compiler.connection.ops.select % sql, params
        return sql, params