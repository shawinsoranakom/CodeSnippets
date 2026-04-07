def get_indexes(self, table):
        """
        Get the indexes on the table using a new cursor.
        """
        with connection.cursor() as cursor:
            return [
                c["columns"][0]
                for c in connection.introspection.get_constraints(
                    cursor, table
                ).values()
                if c["index"] and len(c["columns"]) == 1
            ]