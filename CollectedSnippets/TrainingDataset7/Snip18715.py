def test_get_primary_key_column_pk_constraint(self):
        sql = """
            CREATE TABLE test_primary(
                id INTEGER NOT NULL,
                created DATE,
                PRIMARY KEY(id)
            )
        """
        with connection.cursor() as cursor:
            try:
                cursor.execute(sql)
                field = connection.introspection.get_primary_key_column(
                    cursor,
                    "test_primary",
                )
                self.assertEqual(field, "id")
            finally:
                cursor.execute("DROP TABLE test_primary")