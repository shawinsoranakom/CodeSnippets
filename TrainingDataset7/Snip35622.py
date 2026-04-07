def test_many_to_many_between_unmanaged_and_managed(self):
        """
        An intermediary table between a managed and an unmanaged model should
        be created.
        """
        table = Managed1._meta.get_field("mm").m2m_db_table()
        tables = connection.introspection.table_names()
        self.assertIn(table, tables, "Table '%s' does not exist." % table)