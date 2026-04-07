def test_many_to_many_between_unmanaged(self):
        """
        The intermediary table between two unmanaged models should not be
        created.
        """
        table = Unmanaged2._meta.get_field("mm").m2m_db_table()
        tables = connection.introspection.table_names()
        self.assertNotIn(
            table, tables, "Table '%s' should not exist, but it does." % table
        )