def get_constraints(self, table):
        """Get the constraints on the table using a new cursor."""
        with connection.cursor() as cursor:
            return connection.introspection.get_constraints(cursor, table)