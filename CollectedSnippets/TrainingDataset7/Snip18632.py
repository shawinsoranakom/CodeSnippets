def test_sql_table_creation_raises_with_collation(self):
        settings = {"COLLATION": "test"}
        msg = (
            "PostgreSQL does not support collation setting at database "
            "creation time."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.check_sql_table_creation_suffix(settings, None)