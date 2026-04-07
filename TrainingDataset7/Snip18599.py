def test_get_table_description_view_default_collation(self):
        person_table = connection.introspection.identifier_converter(
            Person._meta.db_table
        )
        first_name_column = connection.ops.quote_name(
            Person._meta.get_field("first_name").column
        )
        person_view = connection.introspection.identifier_converter("TEST_PERSON_VIEW")
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE VIEW {person_view} "
                f"AS SELECT {first_name_column} FROM {person_table}"
            )
            try:
                columns = connection.introspection.get_table_description(
                    cursor, person_view
                )
                self.assertEqual(len(columns), 1)
                self.assertIsNone(columns[0].collation)
            finally:
                cursor.execute(f"DROP VIEW {person_view}")