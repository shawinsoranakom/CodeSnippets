def test_get_storage_engine(self):
        table_name = "test_storage_engine"
        create_sql = "CREATE TABLE %s (id INTEGER) ENGINE = %%s" % table_name
        drop_sql = "DROP TABLE %s" % table_name
        default_connection = connections["default"]
        other_connection = connections["other"]
        try:
            with default_connection.cursor() as cursor:
                cursor.execute(create_sql % "InnoDB")
                self.assertEqual(
                    default_connection.introspection.get_storage_engine(
                        cursor, table_name
                    ),
                    "InnoDB",
                )
            with other_connection.cursor() as cursor:
                cursor.execute(create_sql % "MyISAM")
                self.assertEqual(
                    other_connection.introspection.get_storage_engine(
                        cursor, table_name
                    ),
                    "MyISAM",
                )
        finally:
            with default_connection.cursor() as cursor:
                cursor.execute(drop_sql)
            with other_connection.cursor() as cursor:
                cursor.execute(drop_sql)