def get_sequences(self, cursor, table_name, table_fields=()):
        """
        Return a list of introspected sequences for table_name. Each sequence
        is a dict: {'table': <table_name>, 'column': <column_name>}. An
        optional 'name' key can be added if the backend supports named
        sequences.
        """
        raise NotImplementedError(
            "subclasses of BaseDatabaseIntrospection may require a get_sequences() "
            "method"
        )