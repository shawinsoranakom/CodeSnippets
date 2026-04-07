def get_table_description(self, cursor, table_name):
        """
        Return a description of the table with the DB-API cursor.description
        interface.
        """
        raise NotImplementedError(
            "subclasses of BaseDatabaseIntrospection may require a "
            "get_table_description() method."
        )