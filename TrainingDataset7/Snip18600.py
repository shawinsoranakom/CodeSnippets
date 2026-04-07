def test_get_table_description_materialized_view_non_default_collation(self):
        person_table = connection.introspection.identifier_converter(
            Person._meta.db_table
        )
        first_name_column = connection.ops.quote_name(
            Person._meta.get_field("first_name").column
        )
        person_mview = connection.introspection.identifier_converter(
            "TEST_PERSON_MVIEW"
        )
        collation = connection.features.test_collations.get("ci")
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE MATERIALIZED VIEW {person_mview} "
                f"DEFAULT COLLATION {collation} "
                f"AS SELECT {first_name_column} FROM {person_table}"
            )
            try:
                columns = connection.introspection.get_table_description(
                    cursor, person_mview
                )
                self.assertEqual(len(columns), 1)
                self.assertIsNotNone(columns[0].collation)
                self.assertNotEqual(columns[0].collation, collation)
            finally:
                cursor.execute(f"DROP MATERIALIZED VIEW {person_mview}")