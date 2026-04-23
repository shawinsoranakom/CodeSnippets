def check_sql_table_creation_suffix(self, settings, expected):
        with self.changed_test_settings(**settings):
            creation = DatabaseCreation(connection)
            suffix = creation.sql_table_creation_suffix()
            self.assertEqual(suffix, expected)