def test_get_table_description_nullable(self):
        with connection.cursor() as cursor:
            desc = connection.introspection.get_table_description(
                cursor, Reporter._meta.db_table
            )
        nullable_by_backend = connection.features.interprets_empty_strings_as_nulls
        self.assertEqual(
            [r[6] for r in desc],
            [
                False,
                nullable_by_backend,
                nullable_by_backend,
                nullable_by_backend,
                True,
                True,
                False,
                False,
            ],
        )