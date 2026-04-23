def test_get_primary_key_column(self):
        with connection.cursor() as cursor:
            primary_key_column = connection.introspection.get_primary_key_column(
                cursor, Article._meta.db_table
            )
            pk_fk_column = connection.introspection.get_primary_key_column(
                cursor, District._meta.db_table
            )
        self.assertEqual(primary_key_column, "id")
        self.assertEqual(pk_fk_column, "city_id")