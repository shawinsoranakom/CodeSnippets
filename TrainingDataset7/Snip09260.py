def get_relations(self, cursor, table_name):
        """
        Return a dictionary of
            {
                field_name: (field_name_other_table, other_table, db_on_delete)
            }
        representing all foreign keys in the given table.
        """
        raise NotImplementedError(
            "subclasses of BaseDatabaseIntrospection may require a "
            "get_relations() method."
        )