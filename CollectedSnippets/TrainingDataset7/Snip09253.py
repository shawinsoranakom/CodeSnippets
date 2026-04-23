def get_table_list(self, cursor):
        """
        Return an unsorted list of TableInfo named tuples of all tables and
        views that exist in the database.
        """
        raise NotImplementedError(
            "subclasses of BaseDatabaseIntrospection may require a get_table_list() "
            "method"
        )