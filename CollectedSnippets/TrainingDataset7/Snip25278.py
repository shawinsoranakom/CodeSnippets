def test_postgresql_real_type(self):
        with connection.cursor() as cursor:
            cursor.execute("CREATE TABLE django_ixn_real_test_table (number REAL);")
            desc = connection.introspection.get_table_description(
                cursor, "django_ixn_real_test_table"
            )
            cursor.execute("DROP TABLE django_ixn_real_test_table;")
        self.assertEqual(
            connection.introspection.get_field_type(desc[0][1], desc[0]), "FloatField"
        )