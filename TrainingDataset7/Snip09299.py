def fetch_returned_rows(self, cursor, returning_params):
        """
        Given a cursor object for a DML query with a RETURNING statement,
        return the selected returning rows of tuples.
        """
        return cursor.fetchall()